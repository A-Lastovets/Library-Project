from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from fastapi.openapi.utils import get_openapi
from contextlib import asynccontextmanager
from app.database import engine, Base
from app.models.user import User
from sqlalchemy.ext.asyncio import AsyncSession
from app.routes import auth 
#books, reservations, reviews
from passlib.context import CryptContext
from sqlalchemy import select
from app.core.config import settings
import os

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def createAdmin():
    async with AsyncSession(engine) as session:
        # Отримуємо дані з .env
        adminUsername = os.getenv("ADMIN_USERNAME", "Admin")
        adminLastname = "Admin"
        adminEmail = os.getenv("ADMIN_EMAIL")
        adminPassword = os.getenv("ADMIN_PASS")

        if not adminEmail or not adminPassword:
            print("⚠️  ADMIN_EMAIL або ADMIN_PASS не встановлені в .env! Пропускаємо створення адміністратора.")
            return

        # 🔍 Перевіряємо, чи існує адміністратор з таким email
        result = await session.execute(select(User).where(User.email == adminEmail))
        existingAdmin = result.scalar_one_or_none()

        if existingAdmin:
            print(f"✅ Адміністратор {adminUsername} вже існує. Пропускаємо створення.")
            return

        # Хешуємо пароль
        hashedPassword = pwd_context.hash(adminPassword)

        # 🆕 Створюємо адміністратора
        admin = User(
            firstName=adminUsername,
            lastName=adminLastname,
            email=adminEmail,
            hashedPassword=hashedPassword,
            role="librarian"
        )

        session.add(admin)
        await session.commit()
        print(f"🆕 Адміністратор {adminUsername} створений успішно!")

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)  # 🟢 Спочатку створення таблиць
    await createAdmin()  # 🟢 Тепер створюємо адміна
    yield

# ✅ Оновлений FastAPI без додаткових security параметрів
app = FastAPI(
    lifespan=lifespan,
    title="Library API",
    description="API для управління бібліотекою",
    version="1.0",
    swagger_ui_parameters={"persistAuthorization": True}  # Запам'ятовує токен після авторизації
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.FRONTEND_URL == "*" else [settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],  # Дозволяє всі HTTP-методи (GET, POST, PUT, DELETE тощо)
    allow_headers=["*"],  # Дозволяє всі заголовки
)

# 📌 Додаємо маршрути
app.include_router(auth.router)
# app.include_router(books.router)
# app.include_router(reservations.router)
# app.include_router(reviews.router)
