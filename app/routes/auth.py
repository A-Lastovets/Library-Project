from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import timedelta
from sqlalchemy.future import select
from app.database import get_db
from app.core.cache import redis_client
from app.core.config import settings
from app.models.user import User
from app.schemas.schemas import (
    Token, UserCreate, UserResponse, PasswordResetRequest, PasswordReset
)
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

router = APIRouter(tags=["auth"])

# ✅ Виправлення неправильного URL для авторизації
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# 🔑 Логін користувача (отримання JWT-токена)
@router.post("/token", response_model=Token, status_code=status.HTTP_200_OK)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: AsyncSession = Depends(get_db)
):
    user = await authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    access_token = create_access_token(
        {"sub": str(user.id)}, timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": access_token, "token_type": "bearer"}

# 🆕 Реєстрація користувача
@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user: UserCreate, db: AsyncSession = Depends(get_db)):
    existing_user = await get_user_by_email(db, user.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Email already registered"
        )

    secret_code = user.secret_code.strip() if user.secret_code and user.secret_code.strip() else None
    role = "librarian" if secret_code == settings.SECRET_LIBRARIAN_CODE else "reader"

    return await create_user(db, user, role)

# 📩 Запит на скидання пароля
@router.post("/password-reset-request", status_code=status.HTTP_200_OK)
async def request_password_reset(data: PasswordResetRequest, db: AsyncSession = Depends(get_db)):
    user = await get_user_by_email(db, data.email)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    token = create_password_reset_token(user.email)
    await redis_client.setex(f"password-reset:{user.email}", settings.RESET_TOKEN_EXPIRE_MINUTES * 60, token)
    
    await send_password_reset_email(user.email, token)
    return {"message": "Password reset email sent"}

# 🔑 Скидання пароля
@router.post("/password-reset", status_code=status.HTTP_200_OK)
async def reset_password(data: PasswordReset, db: AsyncSession = Depends(get_db)):
    email = await redis_client.get(f"password-reset:{data.token}")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired token"
        )

    user = await get_user_by_email(db, email.decode())
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    await update_password(db, user.email, data.new_password)
    await redis_client.delete(f"password-reset:{data.token}")

    return {"message": "Password updated successfully"}

# 🆕 Отримання поточного користувача
@router.get("/me", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        role=current_user.role
    )

@router.get("/users", response_model=list[UserResponse], status_code=status.HTTP_200_OK)
async def get_all_users(
    db: AsyncSession = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    print(f"🔍 Поточний користувач: {current_user.username}, Роль: {current_user.role}")  # 👉 Додали логування
    if current_user.role.value != "librarian":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

    result = await db.execute(select(User))
    users = result.scalars().all()
    return users
