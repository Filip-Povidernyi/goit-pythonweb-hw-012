from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from fastapi_mail.errors import ConnectionErrors
from pathlib import Path

from src.services.auth import create_email_token
from src.conf.config import config


conf = ConnectionConfig(
    MAIL_USERNAME=config.MAIL_SMTP_USERNAME,
    MAIL_PASSWORD=config.MAIL_SMTP_PASSWORD,
    MAIL_FROM=config.MAIL_SMTP_FROM,
    MAIL_PORT=587,
    MAIL_SERVER=config.MAIL_SMTP_SERVER,
    MAIL_FROM_NAME="Contacts Management API",
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
    TEMPLATE_FOLDER=Path(__file__).parent / "templates",
)


async def send_email(email: str, username: str, host: str):
    try:
        token_email = create_email_token({"sub": email})
        message = MessageSchema(
            subject="Email Confirmation",
            recipients=[email],
            template_body={
                "host": host,
                "username": username,
                "token": token_email,
            },
            subtype="html",
        )

        fm = FastMail(conf)
        await fm.send_message(message, template_name="email_template.html")
    except ConnectionErrors as e:
        print(f"Failed to send verification email to {email}: {e}")
