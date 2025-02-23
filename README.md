# Library-Project
📂 Структура проєкту

library-project/
│── .gitignore                 # Ігнорування файлів для Git
│── LICENSE                    # Ліцензія проєкту
│── poetry.lock                 # Файл блокування залежностей Poetry
│── pyproject.toml              # Конфігураційний файл Poetry
│── README.md                   # Документація проєкту
│── .env                        # Файл змінних оточення
│── alembic/                    # Папка для міграцій бази даних
│── app/                        # Головна папка застосунку
│   ├── core/                   # Конфігурації та налаштування
│   │   ├── config.py           # Читання .env (налаштування)
│   │   ├── security.py         # Логіка для JWT та хешування паролів
│   ├── models/                 # SQLAlchemy моделі
│   │   ├── base.py             # Базовий клас для моделей
│   │   ├── user.py             # Модель користувачів
│   │   ├── book.py             # Модель книг
│   │   ├── reservation.py      # Модель бронювань
│   ├── schemas/                # Pydantic-схеми для валідації
│   │   ├── user.py             # Схема користувачів
│   │   ├── book.py             # Схема книг
│   │   ├── reservation.py      # Схема бронювань
│   ├── routes/                 # Маршрути FastAPI
│   │   ├── user.py             # Реєстрація, логін
│   │   ├── book.py             # Додавання, редагування, видалення книг
│   │   ├── reservation.py      # Логіка бронювання
│   ├── services/               # Бізнес-логіка
│   │   ├── user_service.py     # Логіка користувачів
│   │   ├── book_service.py     # Логіка книг
│   │   ├── reservation_service.py # Логіка бронювань
│   ├── database.py             # Підключення до БД
│   ├── main.py                 # Головний файл для запуску FastAPI
│── celery_worker.py            # Запуск Celery

🚀 Запуск проєкту

1️⃣ Встановлення залежностей
poetry install

2️⃣ Створення .env файлу
Створи .env файл у корені проєкту та додай змінні:

DATABASE_URL=postgresql://username:password@localhost:5432/library_db
SECRET_KEY="your-secret-key"
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=30
REDIS_URL=redis://localhost:6379/0

3️⃣ Запуск міграцій
poetry run alembic upgrade head

4️⃣ Запуск застосунку
poetry run uvicorn app.main:app --reload

📌 API буде доступне за адресою: http://127.0.0.1:8000
