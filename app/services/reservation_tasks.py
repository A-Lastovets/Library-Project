from celery import Celery
from celery.schedules import crontab
from app.core.config import settings
from app.database import SessionLocal
from app.models.reservation import Reservation
from app.models.user import User
from sqlalchemy import select
from datetime import datetime, timedelta
from app.services.email_tasks import send_due_date_reminder

celery = Celery("reservation_tasks", broker=settings.CELERY_BROKER_URL)

@celery.task
def check_due_dates():
    """Перевіряє бронювання та надсилає нагадування читачам."""
    db = SessionLocal()
    today = datetime.now().date()

    result = db.execute(select(Reservation).where(Reservation.due_date == today + timedelta(days=1)))
    reservations = result.scalars().all()

    for reservation in reservations:
        user = db.get(User, reservation.user_id)
        if user:
            send_due_date_reminder.delay(user.email, reservation.book.title, reservation.due_date)

    db.close()

# Налаштовуємо автоматичний запуск кожного дня
celery.conf.beat_schedule = {
    "send_due_date_reminders": {
        "task": "app.tasks.reservation_tasks.check_due_dates",
        "schedule": crontab(hour=0, minute=0),  # Виконання о 00:00
    },
}
