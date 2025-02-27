from datetime import datetime, timedelta
from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.models.user import User
from app.schemas.schemas import UserCreate
from app.core.config import settings
from app.database import get_db

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/sign-in-swagger")

# 🔹 Отримати користувача за email
async def get_user_by_email(db: AsyncSession, email: str)-> User | None:
    result = await db.execute(select(User).where(User.email == email.lower()))
    return result.scalar_one_or_none()

# 🔹 Аутентифікація користувача
async def authenticate_user(db: AsyncSession, email: str, password: str):
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user or not pwd_context.verify(password, user.hashedPassword):
        return None
    return user

# 🔹 Створення JWT токена
def create_access_token(data: dict, expires_delta: timedelta):
    to_encode = data.copy()
    to_encode.update({"exp": datetime.now() + expires_delta})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

# 🔹 Створення нового користувача
async def create_user(db: AsyncSession, user_data: UserCreate, role: str):
    existing_user = await get_user_by_email(db, user_data.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = pwd_context.hash(user_data.password)

    user = User(
        firstName=user_data.firstName.capitalize(),
        lastName=user_data.lastName.capitalize(),
        email=user_data.email.lower(),
        hashedPassword=hashed_password,
        role=role
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

# 🔹 Створення токена для скидання пароля
def create_password_reset_token(email: str):
    return jwt.encode(
        {"sub": email, "exp": datetime.now() + timedelta(minutes=settings.RESET_TOKEN_EXPIRE_MINUTES)},
        settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )

# 🔹 Оновлення пароля користувача
async def update_password(db: AsyncSession, email: str, new_password: str):
    user = await get_user_by_email(db, email)
    if not user:
        return None

    user.hashed_password = pwd_context.hash(new_password)
    await db.commit()
    return user

# 🟢 Отримання поточного користувача (авторизація через JWT)
async def get_current_user(
    token: str = Depends(oauth2_scheme), 
    db: AsyncSession = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception

    print(f"🔍 Отриманий користувач: {user.firstName}, Роль: {user.role}")
    return user
