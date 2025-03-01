from fastapi import APIRouter, Depends, HTTPException, status
from fastapi import Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import ValidationError
from sqlalchemy import select
from datetime import timedelta
from app.database import get_db
from app.core.cache import redis_client
from app.core.config import settings
from app.models.user import User
from app.schemas.schemas import (Token, LoginRequest, UserCreate, UserResponse, PasswordResetRequest, PasswordReset)
from app.services.user_service import (
    authenticate_user,
    create_access_token,
    create_user,
    get_user_by_email,
    create_password_reset_token,
    update_password,
    get_current_user
)
from app.services.email_tasks import send_password_reset_email
from app.services.validate_pass import validate_password
import logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])

# 🔑 Логін користувача (отримання JWT-токена)
@router.post("/sign-in", response_model=Token, status_code=status.HTTP_200_OK)
async def sign_in(request: Request, login_data: LoginRequest, db: AsyncSession = Depends(get_db)):
    """ ✅ Вхід через JSON """

    raw_body = await request.json()  # Подивимося, що реально приходить
    print("Received raw JSON:", raw_body)

    try:
        login_data = LoginRequest(**raw_body)  # 🔹 Валідую JSON через Pydantic
        print("Parsed LoginRequest:", login_data.model_dump())
    except ValidationError as e:
        print("Validation Error:", e.json())  # Логи для дебагу
        raise HTTPException(status_code=422, detail=e.errors())
    
    user = await authenticate_user(db, login_data.email, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail={
                "error": "InvalidCredentials",
                "message": "Invalid email or password. Please check your credentials and try again.",
                "suggestion": "If you forgot your password, use the password recovery option."
            }
        )

    accessToken = create_access_token(
        {"sub": str(user.id)}, timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    return {
        "accessToken": accessToken,
        "tokenType": "bearer",
        "user": {
            "id": user.id,
            "firstName": user.firstName,
            "lastName": user.lastName,
            "email": user.email,
            "role": user.role.value
        }
    }

# 🔹 Реєстрація користувача
@router.post("/sign-up", response_model=Token, status_code=status.HTTP_201_CREATED)
async def sign_up(user: UserCreate, db: AsyncSession = Depends(get_db)):
    existingUser = await get_user_by_email(db, user.email)
    if existingUser:
        error_detail = {
            "error": "UserAlreadyExists",
            "message": "A user with this email is already registered.",
            "suggestion": "Try logging in or use password recovery."
        }
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_detail)

    # 🔹 Валідація пароля перед створенням користувача
    validate_password(user.password)

    # 🔹 Визначення ролі користувача (лікар або читач)
    role = "librarian" if user.secretCode and user.secretCode.strip() == settings.SECRET_LIBRARIAN_CODE else "reader"

    # 🔹 Створюємо користувача
    createdUser = await create_user(db, user, role)

    # 🔹 Генеруємо токен після реєстрації
    accessToken = create_access_token(
        {"sub": str(createdUser.id)}, timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    return {
        "accessToken": accessToken,
        "tokenType": "bearer",
        "user": {
            "id": createdUser.id,
            "firstName": createdUser.firstName,
            "lastName": createdUser.lastName,
            "email": createdUser.email,
            "role": createdUser.role.value
        }
    }

# 🔹 Запит на скидання пароля
@router.post("/password-recovery", status_code=status.HTTP_200_OK)
async def request_password_reset(data: PasswordResetRequest, db: AsyncSession = Depends(get_db)):
    user = await get_user_by_email(db, data.email)
    # Завжди повертаємо одне й те саме повідомлення для безпеки
    reset_link = None
    if user:
        token = create_password_reset_token(user.email)
        await redis_client.setex(f"password-reset:{token}", settings.RESET_TOKEN_EXPIRE_MINUTES * 60, user.email)
        reset_link = f"{settings.FRONTEND_URL}/reset-password?token={token}"
        send_password_reset_email(user.email, reset_link)

    return {"message": "If an account with that email exists, a password reset email has been sent."}

# 🔹 Скидання пароля (повертаємо оновлену інформацію про користувача)
@router.post("/password-reset", status_code=status.HTTP_200_OK)
async def reset_password(data: PasswordReset, db: AsyncSession = Depends(get_db)):
    try:
        email = await redis_client.get(f"password-reset:{data.token}")
        if not email:
            logger.warning(f"Invalid or expired token: {data.token}")  # 🔹 Лог помилки
            raise HTTPException(status_code=400, detail="Invalid or expired token")
        
        await redis_client.delete(f"password-reset:{data.token}")  # Видаляємо токен перед оновленням

    except Exception as e:
        logger.error(f"Error accessing Redis: {e}")  # 🔹 Лог реальної помилки
        raise HTTPException(status_code=500, detail="Temporary server issue. Try again later.")

    user = await get_user_by_email(db, email)
    if not user:
        logger.warning(f"User not found for email: {email}")  # 🔹 Лог якщо юзера немає
        raise HTTPException(status_code=404, detail="User not found")

    # Валідація пароля
    try:
        validate_password(data.newPassword)
    except ValueError as e:
        logger.warning(f"Invalid password attempt for user {email}: {e}")  # 🔹 Лог валідації
        raise HTTPException(status_code=400, detail=str(e))

    if not await update_password(db, user.email, data.newPassword):
        logger.error(f"Failed to update password for user {email}")  # 🔹 Лог якщо пароль не змінився
        raise HTTPException(status_code=500, detail="Could not update password. Try again later.")

    logger.info(f"Password reset successful for {email}")  # 🔹 Успішне оновлення пароля
    return {"message": "Password has been reset successfully. Please log in again."}

# 🔹 Отримати всіх користувачів (тільки для librarian)
@router.get("/users", response_model=list[UserResponse], status_code=status.HTTP_200_OK)
async def get_all_users(
    db: AsyncSession = Depends(get_db), 
    currentUser: User = Depends(get_current_user)
):
    print(f"🔍 Авторизований користувач: {currentUser.firstName}, роль: {currentUser.role}")

    if currentUser.role.value != "librarian":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

    result = await db.execute(select(User))
    print(f"resultat: {result}")
    users = result.scalars().all()

    return [
        {
            "id": user.id,
            "firstName": user.firstName,
            "lastName": user.lastName,
            "email": user.email,
            "role": user.role.value
        }
        for user in users
    ]

# 🔑 Логін через Swagger UI (OAuth2 Password Flow)
@router.post("/sign-in-swagger", status_code=status.HTTP_200_OK, include_in_schema=False)
async def sign_in_swagger(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """ 🔄 Вхід через Swagger UI (OAuth2 Password Flow) """

    email = form_data.username
    password = form_data.password

    user = await authenticate_user(db, email, password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    access_token = create_access_token(
        {"sub": str(user.id)}, timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",       
    }
