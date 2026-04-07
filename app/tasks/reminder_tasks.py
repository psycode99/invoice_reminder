from uuid import UUID
from app.core.logger_instance import celery_logger as logger
import sentry_sdk
from sqlalchemy import and_, or_, select, text
from app.core.constants import MAX_REMINDERS
from app.db.models.invoice import Invoice
from app.helpers.pg_lock_hash import lock_key
from app.helpers.sentry_helpers.sentry_celery_helper import SentryHelper
from app.mail.build_mail import build_invoice_email
from app.mail.email_escalator import determine_escalation
from app.core.reminder_calc import calculate_next_reminder
from app.tasks.celery_app import celery_app
from app.db.session import SessionLocal
from app.mail.email_sender import send_email, send_email_dev
from datetime import UTC, datetime
from app.core.config import settings
from sqlalchemy.orm import selectinload


@celery_app.task(
    bind=True,
    max_retries=3,
    base=SentryHelper,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
)
def send_invoice_issued_task(self, invoice_id: UUID, request_id):
    db = SessionLocal()
    try:
        # pg advisory lock mechanism in case multiple workers
        lock_id = f"invoice_issued:{invoice_id}"
        lock_hash = lock_key(lock_id)

        acquired = db.execute(
            text("SELECT pg_try_advisory_xact_lock(:id)"), {"id": lock_hash}
        ).scalar_one()

        if not acquired:
            return
        
        stmt = (
            select(Invoice)
            .options(selectinload(Invoice.business))
            .where(Invoice.id == invoice_id)
        )

        invoice = db.execute(stmt).scalar_one()

        subject, msg = build_invoice_email(invoice=invoice, escalation="issued")
        logger_task = logger.bind(invoice_id=str(invoice.id))

        if settings.prod:
            logger_task.info("Sending invoice Issued", request_id=str(request_id))
            send_email(
                to_addr=invoice.customer_email,
                from_addr=settings.from_email_addr,
                subject=subject,
                msg=msg,
                invoice_id=invoice.id,
                type="issued",
            )
        else:
            logger_task.info("Sending invoice Issued", request_id=str(request_id))
            send_email_dev(
                to_addr=invoice.customer_email,
                from_addr=settings.smtp_email,
                subject=subject,
                msg=msg,
                invoice_id=invoice.id,
                type="issued",
            )
        invoice.next_reminder_at = calculate_next_reminder(invoice)

        db.commit()
        logger_task.info("Invoice Issued Successfully", request_id=str(request_id))

    except Exception as e:
        sentry_sdk.capture_exception(e)
        db.rollback()
        raise self.retry(exc=e, countdown=60)

    finally:
        db.close()


@celery_app.task(bind=True, max_retries=3, base=SentryHelper)
def send_invoice_reminder_task(self, invoice_id: UUID):
    db = SessionLocal()
    try:
        # pg advisory lock mechanism in case multiple workers
        lock_id = f"invoice_reminder:{invoice_id}"
        lock_hash = lock_key(lock_id)

        acquired = db.execute(
            text("SELECT pg_try_advisory_xact_lock(:id)"), {"id": lock_hash}
        ).scalar_one()

        if not acquired:
            return

        stmt = (
            select(Invoice)
            .options(selectinload(Invoice.business))
            .where(Invoice.id == invoice_id)
        )

        invoice = db.execute(stmt).scalar_one()

        if invoice.payment_status != "unpaid" or invoice.payment_status != "partial":
            return

        if invoice.reminder_count >= MAX_REMINDERS:
            return

        if not invoice.reminders_enabled or invoice.next_reminder_at > datetime.now(
            UTC
        ):
            return

        escalation = determine_escalation(invoice.reminder_count)

        subject, msg = build_invoice_email(invoice=invoice, escalation=escalation)

        logger_task = logger.bind(invoice_id=str(invoice.id))

        if settings.prod:
            logger_task.info("Sending Invoice Reminder")
            send_email(
                to_addr=invoice.customer_email,
                from_addr=settings.from_email_addr,
                subject=subject,
                msg=msg,
                invoice_id=invoice.id,
                type="reminder",
            )
        else:
            logger_task.info("Sending Invoice Reminder")
            send_email_dev(
                to_addr=invoice.customer_email,
                from_addr=settings.smtp_email,
                subject=subject,
                msg=msg,
                invoice_id=invoice.id,
                type="reminder",
            )

        invoice.reminder_count += 1
        invoice.last_reminder_at = datetime.now(UTC)
        invoice.next_reminder_at = calculate_next_reminder(invoice)

        db.commit()

    except Exception as e:
        sentry_sdk.capture_exception(e)
        db.rollback()
        raise self.retry(exc=e, countdown=60)

    finally:
        db.close()


@celery_app.task
def process_due_reminders():
    db = SessionLocal()
    try:
        now = datetime.now(UTC)

        stmt = select(Invoice).where(
            and_(
                or_(
                    Invoice.payment_status == "unpaid",
                    Invoice.payment_status == "partial",
                ),
                Invoice.reminders_enabled == True,
                Invoice.reminder_count < MAX_REMINDERS,
                Invoice.next_reminder_at <= now,
            )
        )

        invoices = db.execute(stmt).scalars().all()
        for invoice in invoices:
            send_invoice_reminder_task.delay(invoice.id)

    except Exception as e:
        sentry_sdk.capture_exception(e)
        raise

    finally:
        db.close()
