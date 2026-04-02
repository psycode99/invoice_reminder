from datetime import UTC, datetime, timedelta
from loguru import logger
import sentry_sdk
from sqlalchemy.dialects.postgresql import insert
from app.db.models.accounting_integration import AccountingIntegration
from app.db.models import invoice
from app.db.models.webhook_events import WebhookEvent
from app.helpers.errs import MissingBalanceException
from app.helpers.sentry_helpers.sentry_celery_helper import SentryHelper
from app.tasks.celery_app import celery_app
from app.db.session import SessionLocal
from intuitlib.client import AuthClient
from quickbooks import QuickBooks
from app.core.config import settings
from quickbooks.objects import Invoice
from dateutil import parser


@celery_app.task(bind=True, max_retries=3, base=SentryHelper)
def invoice_webhooks_qbo(self, payload: list[dict], request_id):
    db = SessionLocal()
    try:
        invoice_dict = []
        for event in payload:

            realm_id = event.get("intuitaccountid")
            invoice_id = event.get("intuitentityid")

            if not realm_id:
                return

            integration = (
                db.query(AccountingIntegration)
                .filter(
                    AccountingIntegration.company_id == realm_id,
                    AccountingIntegration.provider == "qbo",
                    AccountingIntegration.connected == True,
                )
                .first()
            )

            if not integration:
                logger.warning(
                    "Integration not Found",
                    company_id=realm_id,
                    provider="qbo",
                    request_id=str(request_id),
                )
                return

            logger.info(
                "Initiating Webhooks Task",
                request_id=str(request_id),
                integration="qbo",
                company_id=realm_id,
            )

            stmt = (
                insert(WebhookEvent)
                .values(event_id=event.get("id"), provider="qbo", company_id=realm_id)
                .on_conflict_do_nothing()
            )

            result = db.execute(stmt)

            if result.rowcount == 0:
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

            if event.get("type") == "qbo.invoice.deleted.v1":
                invoice_to_del = (
                    db.query(invoice.Invoice)
                    .filter(
                        invoice.Invoice.external_invoice_id == invoice_id,
                        invoice.Invoice.accounting_integration_id == integration.id,
                    )
                    .first()
                )

                if not invoice_to_del:
                    logger.warning(
                        "Invoice Not Found",
                        integration="qbo",
                        external_invoice_id=invoice_id,
                        request_id=str(request_id),
                    )
                    continue

                db.delete(invoice_to_del)

            elif event.get("type") in {
                "qbo.invoice.created.v1",
                "qbo.invoice.updated.v1",
            }:

                inv = Invoice.get(invoice_id, qb=qb_client)

                if not inv.BillEmail or not getattr(inv.BillEmail, "Address", None):
                    continue
                

                if inv.Balance is None:
                    logger.error(
                        "Invoice Object has no Balance",
                        integration="qbo",
                        business_id=str(integration.business_id),
                        accountung_integration_id=str(integration.id),
                        external_invoice_id=str(inv.id),
                    )
                    raise MissingBalanceException()

                payment_status = None
                if inv.Balance == 0:
                    payment_status = "paid"
                elif inv.Balance < inv.TotalAmt:
                    payment_status = "partial"
                elif inv.Balance >= inv.TotalAmt:
                    payment_status = "unpaid"

                due_date = parser.parse(inv.DueDate).date()
                due_dt = datetime.combine(due_date, datetime.min.time(), tzinfo=UTC)

                now = datetime.now(UTC)
                next_reminder_at = now + timedelta(days=2) if due_dt < now else due_dt

                invoice_dict.append(
                    {
                        "business_id": integration.business_id,
                        "accounting_integration_id": integration.id,
                        "external_invoice_id": inv.Id,
                        "invoice_number": inv.DocNumber,
                        "customer_name": (
                            inv.CustomerRef.name if inv.CustomerRef else None
                        ),
                        "customer_email": inv.BillEmail.Address,
                        "customer_company": inv.CustomerRef.name,
                        "subtotal_amount": next(
                            (
                                line.Amount
                                for line in inv.Line
                                if line.DetailType == "SubTotalLineDetail"
                            ),
                            None,
                        ),
                        "total_amount": inv.TotalAmt,
                        "tax_amount": (
                            inv.TxnTaxDetail.TotalTax if inv.TxnTaxDetail else 0
                        ),
                        "balance": inv.Balance if inv.Balance is not None else 0,
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
                "balance": stmt.excluded.balance,
                "due_date": stmt.excluded.due_date,
                "issue_date": stmt.excluded.issue_date,
                "payment_status": stmt.excluded.payment_status,
                "currency": stmt.excluded.currency,
                "next_reminder_at": stmt.excluded.next_reminder_at,
            },
        )
        if invoice_dict:
            db.execute(stmt)

        db.commit()
        logger.info(
            "Webhooks Task Processed",
            request_id=str(request_id),
            integration="qbo",
            company_id=realm_id,
        )

    except Exception as e:
        sentry_sdk.capture_exception(e)
        db.rollback()
        raise self.retry(exc=e, countdown=60)

    finally:
        db.close()
