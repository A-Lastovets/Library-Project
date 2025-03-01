import logging
from celery import Celery
from app.core.config import settings
from app.services.email_service import send_email

celery = Celery("email_tasks", broker=settings.CELERY_BROKER_URL)

logger = logging.getLogger(__name__)

@celery.task(bind=True, max_retries=3)
def send_password_reset_email(self, email: str, reset_link: str):
    """Надсилає лист для скидання пароля."""
    subject = "Password Reset Request"
    message = f"""
    <html>
        <body>
            <p>Hello,</p>
            <p>You requested a password reset. Click the link below to reset your password:</p>
            <p><a href="{reset_link}" style="font-size: 16px; color: #007bff; text-decoration: none;">Reset Password</a></p>
            <p>If you did not request this, please ignore this email.</p>
        </body>
    </html>
    """
    try:
        send_email(email, subject, message, html=True)
        logger.info(f"Password reset email sent to {email}")
    except Exception as e:
        logger.error(f"Error sending password reset email to {email}: {e}")
        raise self.retry(exc=e, countdown=10)  # Повторна спроба через 10 сек

@celery.task(bind=True, max_retries=3)
def send_reservation_email(self, user_email: str, book_title: str, due_date: str):
    """Надсилає лист про підтвердження бронювання."""
    subject = "Your book reservation is confirmed"
    message = f"""
    Hello,

    Your reservation for the book "{book_title}" has been confirmed.
    The book must be returned by {due_date}.

    Thank you for using our library!
    """
    try:
        send_email(user_email, subject, message)
        logger.info(f"Reservation email sent to {user_email}")
    except Exception as e:
        logger.error(f"Error sending reservation email to {user_email}: {e}")
        raise self.retry(exc=e, countdown=10)

@celery.task(bind=True, max_retries=3)
def send_due_date_reminder(self, user_email: str, book_title: str, due_date: str):
    """Надсилає нагадування про необхідність повернення книги."""
    subject = "Reminder: Book return due soon"
    message = f"""
    Hello,

    Just a friendly reminder that your borrowed book "{book_title}" 
    is due for return on {due_date}.

    Please make sure to return it on time to avoid penalties.

    Thank you for using our library!
    """
    try:
        send_email(user_email, subject, message)
        logger.info(f"Due date reminder email sent to {user_email}")
    except Exception as e:
        logger.error(f"Error sending due date reminder to {user_email}: {e}")
        raise self.retry(exc=e, countdown=10)
