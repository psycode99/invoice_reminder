from typing import Optional
from uuid import UUID
from app.core.messages import INVOICE_NOT_FOUND, NO_INVOICES_FOUND
from app.db.models import Invoice
from sqlalchemy.orm import Session
from fastapi import HTTPException, Response, status


class InvoiceService:
    def create_invoice(self, invoice_data: dict, business_id: UUID, db: Session):
        invoice = Invoice(**invoice_data, business_id=business_id)
        db.add(invoice)
        db.commit()
        db.refresh(invoice)
        return invoice

    def get_invoice(self, id: UUID, business_id: UUID, db: Session):
        invoice = db.query(Invoice).filter_by(id=id, business_id=business_id).first()
        if not invoice:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=INVOICE_NOT_FOUND
            )
        return invoice

    def get_invoices_for_business(self, business_id: UUID, db: Session):
        invoices = db.query(Invoice).filter_by(business_id=business_id).all()
        if not invoices:
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
            raise HTTPException(status_code=404, detail="No invoices found")
        return result

    def update_invoice(
        self, id: UUID, business_id: UUID, db: Session, invoice_data: dict
    ):
        invoice = db.query(Invoice).filter(Invoice.id==id, Invoice.business_id==business_id).first()
        if not invoice:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=INVOICE_NOT_FOUND
            )

        for key, value in invoice_data.items():
            setattr(invoice, key, value)

        db.commit()
        db.refresh(invoice)
        return invoice

    def delete_invoice(self, id: UUID, business_id: UUID, db: Session):
        invoice = db.query(Invoice).filter(Invoice.id==id, Invoice.business_id==business_id).first()
        if not invoice:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=INVOICE_NOT_FOUND
            )
        db.delete(invoice)
        db.commit()
        return Response(status_code=status.HTTP_204_NO_CONTENT)
