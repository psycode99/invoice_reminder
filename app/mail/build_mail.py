from jinja2 import Environment, FileSystemLoader, select_autoescape
from app.db.models.invoice import Invoice

env = Environment(
    loader=FileSystemLoader("app/templates"),
    autoescape=select_autoescape(["html", "xml"]),
)


def build_invoice_email(invoice: Invoice, escalation: str):
    template_map = {
        "issued": "invoice_issued.html",
        "mild": "invoice_mild.html",
        "medium": "invoice_medium.html",
        "stern": "invoice_stern.html",
    }

    template = env.get_template(template_map[escalation])

    context = {
        "customer_name": invoice.customer_name,
        "invoice_number": invoice.invoice_number,
        "subtotal": invoice.subtotal_amount,
        "tax": invoice.tax_amount,
        "total": invoice.total_amount,
        "currency": invoice.currency,
        "issue_date": invoice.issue_date,
        "due_date": invoice.due_date,
        "business_name": invoice.business.name,
        "business_email": invoice.business.email,
    }

    html = template.render(**context)
    
    if escalation == "issued":
        subject = f"Invoice #{invoice.invoice_number} Issued"
    else:
        subject = f"Invoice #{invoice.invoice_number} Reminder"

    return subject, html
