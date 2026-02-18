from uuid import UUID
from loguru import logger
from sqlalchemy import select
from app.core.constants import MAX_REMINDERS
from app.db.models.invoice import Invoice
from app.mail.build_mail import build_invoice_email
from app.mail.email_escalator import determine_escalation
from app.core.reminder_calc import calculate_next_reminder
from app.tasks.celery_app import celery_app
from app.db.session import SessionLocal
from app.mail.email_sender import send_email, send_email_dev
from datetime import UTC, datetime
from app.core.config import settings
from sqlalchemy.orm import selectinload


@celery_app.task(bind=True, max_retries=3)
def send_invoice_issued_task(self, invoice_id: UUID):
    db = SessionLocal()
    try:
        stmt = (
            select(Invoice)
            .options(selectinload(Invoice.business))
            .where(Invoice.id == invoice_id)
        )

        invoice = db.execute(stmt).scalar_one()

        subject, msg = build_invoice_email(invoice=invoice, escalation="issued")

        if settings.prod:
            send_email(
                to_addr=invoice.customer_email,
                from_addr=settings.from_email_addr,
                subject=subject,
                msg=msg,
                invoice_id=invoice.id,
                type="issued"
            )
        else:
            logger_task = logger.bind(invoice_id=str(invoice.id))
            logger_task.info("Sending invoice Issued")

            send_email_dev(
                to_addr=invoice.customer_email,
                from_addr=settings.smtp_email,
                subject=subject,
                msg=msg,
                invoice_id=invoice.id,
                type="issued"
            )
        invoice.next_reminder_at = calculate_next_reminder(invoice)

        db.commit()

    except Exception as e:
        db.rollback()
        raise self.retry(exc=e, countdown=60)

    finally:

        db.close()


@celery_app.task(bind=True, max_retries=3)
def send_invoice_reminder_task(self, invoice_id: UUID):
    db = SessionLocal()
    try:
        stmt = (
            select(Invoice)
            .options(selectinload(Invoice.business))
            .where(Invoice.id == invoice_id)
        )

        invoice = db.execute(stmt).scalar_one()

        if invoice.payment_status != "unpaid":
            return

        if invoice.reminder_count >= MAX_REMINDERS:
            return

        if (
            not invoice.reminders_enabled
            or invoice.next_reminder_at > datetime.now(UTC)
        ):
            return

        escalation = determine_escalation(invoice.reminder_count)

        subject, msg = build_invoice_email(invoice=invoice, escalation=escalation)

        if settings.prod:
            send_email(
                to_addr=invoice.customer_email,
                from_addr=settings.from_email_addr,
                subject=subject,
                msg=msg,
                invoice_id=invoice.id,
                type="issued"
            )
        else:
            send_email_dev(
                to_addr=invoice.customer_email,
                from_addr=settings.smtp_email,
                subject=subject,
                msg=msg,
                invoice_id=invoice.id,
                type="issued"
            )

        invoice.reminder_count += 1
        invoice.last_reminder_at = datetime.now(UTC)
        invoice.next_reminder_at = calculate_next_reminder(invoice)

        db.commit()

    except Exception as e:
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
            Invoice.payment_status == "unpaid",
            Invoice.reminders_enabled == True,
            Invoice.reminder_count < MAX_REMINDERS,
            Invoice.next_reminder_at <= now,
        )

        invoices = db.execute(stmt).scalars().all()
        for invoice in invoices:
            send_invoice_reminder_task.delay(invoice.id)

    finally:
        db.close()
