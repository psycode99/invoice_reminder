from app.db.models.invoice import Invoice
from sentry_sdk import set_context, configure_scope

def attach_invoice_partial_context(invoice: Invoice):

    with configure_scope() as scope:
        scope.set_tag("business_id", invoice.business_id)

    set_context(
        "invoice_input", {
            "business_id": invoice.business_id,
            "status": invoice.status,
            "accounting_integration_id": invoice.accounting_integration_id,
            "external_invoice_id": invoice.external_invoice_id,
        }
    )

def attach_invoice_full_context(invoice: Invoice):

    with configure_scope() as scope:
        scope.set_tag("invoice_id", invoice.id)

    set_context(
        "invoice", {
            "invoice_id": invoice.id,
            "business_id": invoice.business_id,
            "status": invoice.status,
            "accounting_integration_id": invoice.accounting_integration_id,
            "external_invoice_id": invoice.external_invoice_id,
            "created_at": invoice.created_at,
            "updated_at": invoice.updated_at
        }
    )