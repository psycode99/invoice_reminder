from uuid import UUID
import resend
from app.core.config import settings
from loguru import logger

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
        logger.exception(f"Failed to Send Invoice {type.upper()}", invoice_id=str(invoice_id))
        raise
