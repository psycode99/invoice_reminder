from datetime import UTC, datetime, timedelta
from uuid import UUID
from intuitlib.client import AuthClient
from loguru import logger
from quickbooks.objects import Invoice
from quickbooks import QuickBooks
from app.db.models.accounting_integration import AccountingIntegration
from app.db.session import SessionLocal
from app.db.models import invoice
from sqlalchemy.dialects.postgresql import insert
from app.tasks.celery_app import celery_app
from app.core.config import settings
from dateutil import parser


@celery_app.task(bind=True, max_retries=3)
def sync_qbo_invoices(self, business_id: UUID, accounting_integration_id: UUID):
    db = SessionLocal()
    try:

        integration = (
            db.query(AccountingIntegration)
            .filter(
                AccountingIntegration.provider == "qbo",
                AccountingIntegration.id == accounting_integration_id,
                AccountingIntegration.business_id == business_id,
            )
            .first()
        )

        if not integration:
            logger.warning(
                "Integration Not Found",
                business_id=str(business_id),
                provider="qbo",
                accounting_integration_id=str(accounting_integration_id),
            )
            return

        auth_client = AuthClient(
            client_id=settings.qbo_client_id,
            client_secret=settings.qbo_client_secret,
            redirect_uri=settings.qbo_redirect_uri,
            environment=settings.qbo_environment,
        )

        if integration.expires_at <= datetime.now(UTC) + timedelta(minutes=5):
            auth_client.refresh(integration.refresh_token)

            integration.access_token = auth_client.access_token
            integration.refresh_token = auth_client.refresh_token

            db.commit()
            db.refresh(integration)

        qb_client = QuickBooks(
            auth_client=auth_client,
            refresh_token=integration.refresh_token,
            company_id=integration.company_id,
        )

        qb_invoices = []
        start_point = 1
        batch_size = 1000
        if integration.last_synced_at:

            while True:
                query_ = f"""
                                SELECT * FROM Invoice
                                WHERE MetaData.LastUpdatedTime > '{integration.last_synced_at.isoformat()}'
                                STARTPOSITION {start_point}
                                MAXRESULTS {batch_size}
                        """

                batch = Invoice.query(
                    query_,
                    qb=qb_client,
                )
                if not batch:
                    logger.warning(
                        "No Invoices to Sync",
                        integration="qbo",
                        integration_id=integration.id,
                    )
                    break

                qb_invoices.extend(batch)

                if len(batch) < batch_size:
                    break

                start_point += batch_size
        else:

            while True:
                batch = Invoice.all(
                    start_position=start_point, max_results=batch_size, qb=qb_client
                )
                if not batch:
                    logger.warning(
                        "No Invoices to Sync",
                        integration="qbo",
                        integration_id=integration.id,
                    )
                    break

                qb_invoices.extend(batch)

                if len(batch) < batch_size:
                    break

                start_point += batch_size

        invoice_dict = []
        for inv in qb_invoices:
            if not inv.BillEmail or not getattr(inv.BillEmail, "Address", None):
                continue

            payment_status = None
            if inv.Balance == 0:
                payment_status = "paid"
            elif inv.Balance < inv.TotalAmt:
                payment_status = "partial"
            else:
                payment_status = "unpaid"

            due_date = parser.parse(inv.DueDate).date()
            due_dt = datetime.combine(due_date, datetime.min.time(), tzinfo=UTC)

            now = datetime.now(UTC)
            next_reminder_at = now + timedelta(days=2) if due_dt < now else due_dt

            invoice_dict.append(
                {
                    "business_id": business_id,
                    "accounting_integration_id": accounting_integration_id,
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

        if qb_invoices:
            max_updated = max(inv.MetaData.LastUpdatedTime for inv in qb_invoices)
            max_updated = parser.isoparse(max_updated)
            if max_updated.tzinfo is None:
                max_updated = max_updated.replace(tzinfo=UTC)

            integration.last_synced_at = max_updated

        db.commit()

    except Exception as e:
        db.rollback()
        raise self.retry(exc=e, countdown=60)

    finally:
        db.close()
