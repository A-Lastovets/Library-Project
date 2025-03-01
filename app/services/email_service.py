import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.config import settings

logger = logging.getLogger(__name__)

class EmailClient:
    """Контекстний менеджер для SMTP-з'єднання."""

    def __init__(self):
        self.server = None

    def __enter__(self):
        try:
            if settings.SMTP_PORT == 587:
                self.server = smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT)
                self.server.starttls()
            elif settings.SMTP_PORT == 465:
                self.server = smtplib.SMTP_SSL(settings.SMTP_SERVER, settings.SMTP_PORT)
            else:
                raise ValueError("Unsupported SMTP port. Use 587 (TLS) or 465 (SSL).")

            self.server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            return self.server
        except Exception as e:
            logger.error(f"Failed to connect to SMTP server: {e}")
            raise

    def __exit__(self, exc_type, exc_value, traceback):
        if self.server:
            self.server.quit()

def send_email(to_email: str, subject: str, message: str, html=False):
    """Функція для надсилання email з використанням контекстного менеджера."""
    try:
        msg = MIMEMultipart()
        msg["From"] = settings.EMAIL_FROM
        msg["To"] = to_email
        msg["Subject"] = subject

        footer = """
        --
        This is an automated message. Please do not reply.

        - Your Support Team
        """

        if html:
            full_message = f"{message}<br><br><p>--<br>This is an automated message. Please do not reply.<br><br>- Your Support Team</p>"
            msg.attach(MIMEText(full_message, "html"))
        else:
            msg.attach(MIMEText(message + footer, "plain"))

        with EmailClient() as server:
            server.sendmail(settings.EMAIL_FROM, to_email, msg.as_string())

        logger.info(f"Email sent successfully to {to_email}")
        return {"message": "Email sent successfully"}
    
    except smtplib.SMTPException as e:
        logger.error(f"SMTP error: {e}")
        return {"error": f"SMTP error: {e}"}
    except Exception as e:
        logger.error(f"General email error: {e}")
        return {"error": f"General error: {e}"}
