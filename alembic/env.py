import os
from logging.config import fileConfig
from sqlalchemy import create_engine, pool
from alembic import context
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("❌ DATABASE_URL is not set in the environment variables!")

SYNC_DATABASE_URL = DATABASE_URL.replace("postgresql+asyncpg", "postgresql+psycopg2")

# Налаштовуємо конфігурацію Alembic
config = context.config
config.set_main_option("sqlalchemy.url", SYNC_DATABASE_URL)

# Налаштовуємо логування, якщо є файл конфігурації
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 🟢 Явний імпорт всіх моделей
from app.models.base import Base
from app.models.user import User
# from app.models.book import Book
# from app.models.review import Review
# from app.models.reservation import Reservation

# Призначаємо всі метаданні для Alembic
target_metadata = Base.metadata

def run_migrations_offline():
    """Виконання міграцій у 'offline' режимі."""
    context.configure(
        url=SYNC_DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    """Виконання міграцій у 'online' режимі."""
    connectable = create_engine(SYNC_DATABASE_URL, poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
