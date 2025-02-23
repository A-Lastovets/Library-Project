import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.config import settings

def send_email(to_email: str, subject: str, message: str):
    """Функція для надсилання email."""
    try:
        msg = MIMEMultipart()
        msg["From"] = settings.EMAIL_FROM  # ✅ Оновлено
        msg["To"] = to_email
        msg["Subject"] = subject

        msg.attach(MIMEText(message, "plain"))

        # 🔹 Визначаємо протокол: TLS (587) або SSL (465)
        if settings.SMTP_PORT == 587:
            server = smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT)
            server.starttls()  # Використовуємо TLS
        elif settings.SMTP_PORT == 465:
            server = smtplib.SMTP_SSL(settings.SMTP_SERVER, settings.SMTP_PORT)  # Використовуємо SSL
        else:
            raise ValueError("Unsupported SMTP port. Use 587 (TLS) or 465 (SSL).")

        # 🔹 Логін в SMTP-сервер
        server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)  # ✅ Оновлено

        # 🔹 Надсилаємо email
        server.sendmail(settings.EMAIL_FROM, to_email, msg.as_string())
        server.quit()

        return {"message": "Email sent successfully"}
    except smtplib.SMTPException as e:
        return {"error": f"SMTP error: {e}"}
    except Exception as e:
        return {"error": f"General error: {e}"}
