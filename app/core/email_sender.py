from uuid import UUID
import resend
from app.core.config import Settings
from loguru import logger

resend.api_key = Settings.resend_api_key


def send_email_invoice_reminder(
    to_addr: str, from_addr: str, subject: str, msg: str, invoice_id: UUID
):
    try:
        logger.info("Sending Invoice Reminder", invoice_id=str(invoice_id))
        resp = resend.Emails.send(
            {"from": from_addr, "to": to_addr, "subject": subject, "html": msg}
        )
        return resp
    except Exception as e:
        logger.exception("failed to Send Invoice Reminder", invoice_id=str(invoice_id))
        raise
