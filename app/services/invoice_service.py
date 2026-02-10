from app.core.messages import INVOICE_NOT_FOUND, NO_INVOICES_FOUND
from app.db.models import Invoice
from sqlalchemy.orm import Session
from sqlalchemy import update
from typing import List
from fastapi import HTTPException, Response, status


class InvoiceService():
    def create_invoice(self, invoice_data: dict, db: Session):
        invoice = Invoice(**invoice_data)
        db.add(invoice)
        db.commit()
        db.refresh(invoice)

    def get_invoice(self, id: str, business_id: str, db: Session):
        invoice = db.query(Invoice).filter_by(id=id, business_id=business_id).first()
        if not invoice:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=INVOICE_NOT_FOUND)
        return invoice
    
    def get_invoices_for_business(self, business_id: str, db: Session):
        invoices = db.query(Invoice).filter_by(business_id=business_id).all()
        if not invoices:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=NO_INVOICES_FOUND)
        return invoices

    def search_invoice(self, invoice_number: str, business_id: str, db: Session):
        invoice = db.query(Invoice).filter(invoice_number=invoice_number, business_id=business_id).first()
        if not invoice:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=INVOICE_NOT_FOUND)
        return invoice
    
    def update_invoice(self, id: str, business_id: str, db: Session, invoice_data: dict):
        invoice = db.query(Invoice).filter(id=id, business_id=business_id).first()
        if not invoice:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=INVOICE_NOT_FOUND)

        for key, value in invoice_data.items():
            setattr(invoice, key, value)

        db.commit()
        db.refresh(invoice)
        return invoice
    
    def delete_invoice(self, id: str, business_id: str, db: Session):
        invoice = db.query(Invoice).filter(id=id, business_id=business_id).first()
        if not invoice:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=INVOICE_NOT_FOUND)
        db.delete(invoice)
        db.commit()
        return Response(status_code=status.HTTP_204_NO_CONTENT)