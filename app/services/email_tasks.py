'''
Email tasks
'''
from celery import Celery
from app.core.config import settings
from app.services.email_service import send_email

celery = Celery("email_tasks", broker=settings.CELERY_BROKER_URL)

@celery.task
def send_password_reset_email(email: str, reset_link: str):
    """Надсилає лист для скидання пароля."""
    subject = "Password Reset Request"
    message = f"""
    Hello,
    
    You requested a password reset. Click the link below to reset your password:
    {reset_link}
    
    If you did not request this, please ignore this email.
    """
    send_email(email, subject, message)

@celery.task
def send_reservation_email(user_email: str, book_title: str, due_date: str):
    """Надсилає лист про підтвердження бронювання."""
    subject = "Your book reservation is confirmed"
    message = f"""
    Hello,

    Your reservation for the book "{book_title}" has been confirmed.
    The book must be returned by {due_date}.

    Thank you for using our library!
    """
    send_email(user_email, subject, message)

@celery.task
def send_due_date_reminder(user_email: str, book_title: str, due_date: str):
    """Надсилає нагадування про необхідність повернення книги."""
    subject = "Reminder: Book return due soon"
    message = f"""
    Hello,

    Just a friendly reminder that your borrowed book "{book_title}" 
    is due for return on {due_date}.

    Please make sure to return it on time to avoid penalties.

    Thank you for using our library!
    """
    send_email(user_email, subject, message)
