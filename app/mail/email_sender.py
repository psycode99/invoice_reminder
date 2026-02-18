from uuid import UUID
import resend
from app.core.config import settings
from loguru import logger
import smtplib
from email.message import EmailMessage
from app.core.config import settings

resend.api_key = settings.resend_api_key


def send_email(
    to_addr: str, from_addr: str, subject: str, msg: str, invoice_id: UUID, type: str
):
    try:
        logger.info(f"Sending Invoice {type.upper()}", invoice_id=str(invoice_id))
        resp = resend.Emails.send(
            {"from": from_addr, "to": to_addr, "subject": subject, "html": msg}
        )
        return resp
    except Exception as e:
        logger.exception(
            f"Failed to Send Invoice {type.upper()}", invoice_id=str(invoice_id)
        )
        raise


def send_email_dev(
    to_addr: str,
    from_addr: str,
    subject: str,
    msg: str,
    invoice_id,
    type,
):
    email = EmailMessage()
    email["From"] = from_addr
    email["To"] = to_addr
    email["Subject"] = subject

    # HTML body
    email.add_alternative(msg, subtype="html")

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as smtp:
        smtp.starttls()
        smtp.login(settings.smtp_email, settings.smtp_password)
        logger.info(f"Sending Invoice {type.upper()}", invoice_id=str(invoice_id))
        smtp.send_message(email)
