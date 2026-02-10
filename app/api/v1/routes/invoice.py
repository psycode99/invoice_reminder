from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.v1.dependencies import get_db
from app.core.security import get_current_user_dependency
from app.schemas.invoice_schema import InvoiceCreate, InvoiceResponse, InvoiceUpdate
from app.services.business_service import BusinessService
from app.services.invoice_service import InvoiceService


router = APIRouter(prefix="/v1/invoices", tags=["Invoice"])
invoice_service = InvoiceService()
business_service = BusinessService()


@router.post(
    "/{business_id}",
    status_code=status.HTTP_201_CREATED,
    response_model=InvoiceResponse,
)
def create_invoice(
    invoice_data: InvoiceCreate,
    business_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_dependency),
):
    business_service.get_business(id=business_id, db=db, owner_id=current_user.id)
    return invoice_service.create_invoice(
        invoice_data=invoice_data.model_dump(), business_id=business_id, db=db
    )


@router.get(
    "/{business_id}/{invoice_id}",
    status_code=status.HTTP_200_OK,
    response_model=InvoiceResponse,
)
def get_invoice(
    business_id: UUID,
    invoice_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_dependency),
):
    business_service.get_business(id=business_id, db=db, owner_id=current_user.id)
    return invoice_service.get_invoice(id=invoice_id, business_id=business_id, db=db)


@router.get(
    "/{business_id}",
    status_code=status.HTTP_200_OK,
    response_model=List[InvoiceResponse],
)
def get_invoices(
    business_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_dependency),
):
    business_service.get_business(id=business_id, db=db, owner_id=current_user.id)
    return invoice_service.get_invoices_for_business(business_id=business_id, db=db)


@router.get(
    "/{business_id}/search",
    status_code=status.HTTP_200_OK,
    response_model=List[InvoiceResponse],
)
def search_invoice(
    business_id: UUID,
    invoice_number: Optional[str] = Query(None, description="Invoice number to search"),
    customer_name: Optional[str] = Query(None, description="Customer name to search"),
    customer_email: Optional[str] = Query(None, description="Customer email to search"),
    issue_date: Optional[str] = Query(None, description="Issue date YYYY-MM-DD"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_dependency),
):

    business_service.get_business(id=business_id, db=db, owner_id=current_user.id)

    return invoice_service.search_invoice(
        invoice_number=invoice_number,
        customer_name=customer_name,
        customer_email=customer_email,
        issue_date=issue_date,
        business_id=business_id,
        db=db,
    )


@router.put(
    "/{business_id}/{invoice_id}",
    status_code=status.HTTP_200_OK,
    response_model=InvoiceResponse,
)
def update_invoice(
    invoice_data: InvoiceUpdate,
    business_id: UUID,
    invoice_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_dependency),
):
    business_service.get_business(id=business_id, db=db, owner_id=current_user.id)
    return invoice_service.update_invoice(
        id=invoice_id, business_id=business_id, db=db, invoice_data=invoice_data.model_dump(exclude_unset=True)
    )


@router.delete("/{business_id}/{invoice_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_invoice(
    business_id: UUID,
    invoice_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_dependency),
):
    business_service.get_business(id=business_id, db=db, owner_id=current_user.id)
    return invoice_service.delete_invoice(id=invoice_id, business_id=business_id, db=db)
