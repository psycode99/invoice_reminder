from app.db.models.invoice import Invoice
from datetime import timedelta


def calculate_next_reminder(invoice: Invoice):
    if invoice.next_reminder_at == None:
        next_reminder = invoice.due_date
    else:
        next_reminder = invoice.next_reminder_at + timedelta(days=2)
    return next_reminder
