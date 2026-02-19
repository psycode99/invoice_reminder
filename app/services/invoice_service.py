from typing import Optional
from uuid import UUID
from app.core.messages import INVOICE_NOT_FOUND, NO_INVOICES_FOUND
from app.db.models import Invoice
from sqlalchemy.orm import Session
from fastapi import HTTPException, Response, status
from app.tasks.reminder_tasks import send_invoice_issued_task
from loguru import logger


class InvoiceService:
    def create_invoice(self, invoice_data: dict, business_id: UUID, db: Session):
        logger.info(
            "Creating Invoice",
            invoice_number=invoice_data.get("invoice_number"),
            business_id=str(business_id),
        )
        next_reminder_at = invoice_data.get("due_date")
        invoice = Invoice(
            **invoice_data, business_id=business_id
        )
        invoice.next_reminder_at = next_reminder_at
        db.add(invoice)
        db.commit()
        db.refresh(invoice)
        logger.info("Invoice Created", invoice_id=str(invoice.id))

        send_invoice_issued_task.delay(invoice.id)
        return invoice

    def get_invoice(self, id: UUID, business_id: UUID, db: Session):
        logger.info(
            "Fetching Invoice",
            invoice_id=str(id),
            business_id=str(business_id),
        )

        invoice = db.query(Invoice).filter_by(id=id, business_id=business_id).first()
        if not invoice:
            logger.warning(
                "Invoice not Found",
                invoice_id=str(id),
                business_id=str(business_id),
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=INVOICE_NOT_FOUND
            )
        return invoice

    def get_invoices_for_business(self, business_id: UUID, db: Session):
        logger.info("Fetching Invoices", business_id=str(business_id))

        invoices = (
            db.query(Invoice)
            .filter(Invoice.business_id == business_id)
            .order_by(Invoice.created_at.desc())
        )
        if not invoices:
            logger.warning("Invoices not Found", business_id=str(business_id))
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=NO_INVOICES_FOUND
            )
        return invoices

    def search_invoice(
        self,
        business_id: UUID,
        db: Session,
        invoice_number: Optional[str] = None,
        customer_name: Optional[str] = None,
        customer_email: Optional[str] = None,
        issue_date: Optional[str] = None,
    ):
        logger.info("Searching Invoices", business_id=str(business_id))
        query = db.query(Invoice).filter(Invoice.business_id == business_id)

        if invoice_number:
            query = query.filter(Invoice.invoice_number == invoice_number)
        if customer_name:
            query = query.filter(Invoice.customer_name.ilike(f"%{customer_name}%"))
        if customer_email:
            query = query.filter(Invoice.customer_email.ilike(f"%{customer_email}%"))
        if issue_date:
            query = query.filter(Invoice.issue_date == issue_date)

        result = query.all()
        if not result:
            logger.warning("Invoices not Found", business_id=str(business_id))
            raise HTTPException(status_code=404, detail="No invoices found")
        return query

    def update_invoice(
        self, id: UUID, business_id: UUID, db: Session, invoice_data: dict
    ):
        logger.info(
            "Updating invoice",
            invoice_id=str(id),
            business_id=str(business_id),
        )
        invoice = (
            db.query(Invoice)
            .filter(Invoice.id == id, Invoice.business_id == business_id)
            .first()
        )
        if not invoice:
            logger.warning(
                "Invoice not Found",
                invoice_id=str(id),
                business_id=str(business_id),
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=INVOICE_NOT_FOUND
            )

        for key, value in invoice_data.items():
            setattr(invoice, key, value)

        db.commit()
        db.refresh(invoice)
        logger.info(
            "Invoice Updated",
            invoice_id=str(invoice.id),
            business_id=str(business_id),
        )
        return invoice

    def delete_invoice(self, id: UUID, business_id: UUID, db: Session):
        logger.info(
            "Deleting Invoice",
            invoice_id=str(id),
            business_id=str(business_id),
        )
        invoice = (
            db.query(Invoice)
            .filter(Invoice.id == id, Invoice.business_id == business_id)
            .first()
        )
        if not invoice:
            logger.warning(
                "Invoice not Found",
                invoice_id=str(id),
                business_id=str(business_id),
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=INVOICE_NOT_FOUND
            )
        db.delete(invoice)
        db.commit()
        logger.info(
            "Invoice Deleted",
            invoice_id=str(id),
            business_id=str(business_id),
        )
        return Response(status_code=status.HTTP_204_NO_CONTENT)
