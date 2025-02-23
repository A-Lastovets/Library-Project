from fastapi import FastAPI
from fastapi.security import OAuth2PasswordBearer
from contextlib import asynccontextmanager
from app.database import engine, Base
from app.models.user import User
from sqlalchemy.ext.asyncio import AsyncSession
from app.routes import auth, books, reservations, reviews
from passlib.context import CryptContext
from sqlalchemy import select
import os

# 🛡️ Додаємо підтримку Bearer Token для Swagger
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def create_admin():
    async with AsyncSession(engine) as session:
        result = await session.execute(select(User).where(User.username == "admin"))
        if not result.scalars().first():
            hashed_password = pwd_context.hash(os.getenv("ADMIN_PASS", "admin"))
            admin = User(
                username="admin",
                email="admin@library.com",
                hashed_password=hashed_password,
                role="librarian"
            )
            async with session.begin():
                session.add(admin)

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)  # 🟢 Спочатку створення таблиць
    await create_admin()  # 🟢 Тепер створюємо адміна
    yield

# ✅ Оновлений FastAPI без додаткових security параметрів
app = FastAPI(
    lifespan=lifespan,
    title="Library API",
    description="API для управління бібліотекою",
    version="1.0",
    swagger_ui_parameters={"persistAuthorization": True}  # Запам'ятовує токен після авторизації
)

# 📌 Додаємо маршрути
app.include_router(auth.router)
app.include_router(books.router)
app.include_router(reservations.router)
app.include_router(reviews.router)
