from datetime import UTC, datetime, timedelta

from loguru import logger
from sqlalchemy import insert
from app.db.models.accounting_integration import AccountingIntegration
from app.db.models import invoice
from app.tasks.celery_app import celery_app
from app.db.session import SessionLocal
from intuitlib.client import AuthClient
from quickbooks import QuickBooks
from app.core.config import settings
from quickbooks.objects import Invoice
from dateutil import parser


@celery_app.task(bind=True, max_retries=3)
def invoice_webhooks_qbo(self, payload: dict):
    db = SessionLocal()
    try:
        data: dict = payload.get("data")
        realm_id = data.get("realmId")
        event_notifications: list[dict] = data.get("eventNotifications")

        integration = (
            db.query(AccountingIntegration)
            .filter(
                AccountingIntegration.company_id == realm_id,
                AccountingIntegration.provider == "qbo",
            )
            .first()
        )

        if not integration:
            logger.warning("Integration not Found", company_id=realm_id, provider="qbo")
            return

        auth_client = AuthClient(
            client_id=settings.qbo_client_id,
            client_secret=settings.qbo_client_secret,
            redirect_uri=settings.qbo_redirect_uri,
            environment=settings.qbo_environment,
        )

        qb_client = QuickBooks(
            auth_client=auth_client,
            refresh_token=integration.refresh_token,
            company_id=integration.company_id,
        )

        to_delete_ids = []
        invoice_ids = []

        to_insert_dict = []
        invoice_dict = []

        for event in event_notifications:
            if event.get("operation") == "Delete":
                to_delete_ids.append(event.get("id"))
            elif event.get("operation") in {"Create", "Update"}:
                invoice_ids.append(event.get("id"))

        if to_delete_ids:
            for i in to_delete_ids:
                invoice_to_del = (
                    db.query(invoice.Invoice)
                    .filter(
                        invoice.Invoice.external_invoice_id == i,
                        invoice.Invoice.accounting_integration_id == integration.id,
                    )
                    .first()
                )

                if not invoice_to_del:
                    logger.warning(
                        "Invoice Not Found", integration="qbo", external_invoice_id=i
                    )
                    continue

                db.delete(invoice_to_del)

        if invoice_ids:
            query = f""" SELECT * FROM Invoice WHERE Id IN ({','.join(invoice_ids)})"""
            invoice_objects = Invoice.query(query, qb=qb_client)
            to_insert_dict.extend(invoice_objects)

        for inv in to_insert_dict:
            if not inv.BillEmail or not getattr(inv.BillEmail, "Address", None):
                continue

            payment_status = None
            if inv.Balance == 0:
                payment_status = "paid"
            elif inv.Balance < inv.TotalAmt:
                payment_status = "partial"
            else:
                payment_status = "unpaid"

            due = inv.DueDate
            if isinstance(due, datetime):
                due_dt = due
            else:
                due_dt = datetime.combine(due, datetime.min.time(), tzinfo=UTC)

            now = datetime.now(UTC)
            next_reminder_at = now + timedelta(days=2) if due_dt < now else due_dt

            invoice_dict.append(
                {
                    "business_id": integration.business_id,
                    "accounting_integration_id": integration.id,
                    "external_invoice_id": inv.Id,
                    "invoice_number": inv.DocNumber,
                    "customer_name": inv.CustomerRef.name if inv.CustomerRef else None,
                    "customer_email": inv.BillEmail.Address,
                    "customer_company": inv.CustomerRef.name,
                    "subtotal_amount": sum(
                        getattr(line, "Amount", 0)
                        for line in inv.Line
                        if getattr(line, "Amount", None)
                    ),
                    "total_amount": inv.Balance,
                    "tax_amount": inv.TxnTaxDetail.TotalTax if inv.TxnTaxDetail else 0,
                    "issue_date": inv.TxnDate,
                    "due_date": inv.DueDate,
                    "currency": inv.CurrencyRef.value if inv.CurrencyRef else "USD",
                    "payment_status": payment_status,
                    "next_reminder_at": next_reminder_at,
                }
            )

        stmt = insert(invoice.Invoice).values(invoice_dict)

        stmt = stmt.on_conflict_do_update(
            index_elements=[
                "accounting_integration_id",
                "external_invoice_id",
            ],
            set_={
                "invoice_number": stmt.excluded.invoice_number,
                "customer_name": stmt.excluded.customer_name,
                "customer_company": stmt.excluded.customer_company,
                "customer_email": stmt.excluded.customer_email,
                "subtotal_amount": stmt.excluded.subtotal_amount,
                "tax_amount": stmt.excluded.tax_amount,
                "total_amount": stmt.excluded.total_amount,
                "due_date": stmt.excluded.due_date,
                "issue_date": stmt.excluded.issue_date,
                "payment_status": stmt.excluded.payment_status,
                "currency": stmt.excluded.currency,
                "next_reminder_at": stmt.excluded.due_date,
            },
        )
        if invoice_dict:
            db.execute(stmt)

        db.commit()

    except Exception as e:
        db.rollback()
        raise self.retry(exc=e, countdown=60)

    finally:
        db.close()
