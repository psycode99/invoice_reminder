import json
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query, Request, status
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from fastapi_pagination import Page, Params
from fastapi_pagination.ext.sqlalchemy import paginate

from app.core.redis import redis_client
from app.api.v1.dependencies import get_db
from app.core.security import get_current_user_dependency
from app.helpers.idempotency import idempotency_checker
from app.schemas.invoice_schema import InvoiceCreate, InvoiceResponse, InvoiceUpdate
from app.services.business_service import BusinessService
from app.services.invoice_service import InvoiceService
from app.main import limiter

router = APIRouter(prefix="/v1/invoices", tags=["Invoice"])
invoice_service = InvoiceService()
business_service = BusinessService()


@router.post(
    "/{business_id}",
    status_code=status.HTTP_201_CREATED,
    response_model=InvoiceResponse,
)
@limiter.limit("20/minute")
async def create_invoice(
    request: Request,
    invoice_data: InvoiceCreate,
    business_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_dependency),
):
    await business_service.validate_user_owns_business(business_id=business_id, db=db, owner_id=current_user.id)

    idemp_resp = await idempotency_checker(
        request, redis_client, current_user.id
    )

    if idemp_resp.get("status") == "cached":
        return idemp_resp.get("response")

    resp = invoice_service.create_invoice(
        invoice_data=invoice_data.model_dump(mode="json"),
        business_id=business_id,
        db=db,
        request=request,
    )

    data = jsonable_encoder(resp)

    await redis_client.set(
        idemp_resp.get("redis_key"),
        json.dumps(
            {"status": "completed", "payload_hash": idemp_resp.get("hashed_body"), "response": data}
        ),
        ex=86400,
    )

    return resp


@router.get(
    "/{business_id}/search",
    status_code=status.HTTP_200_OK,
    response_model=Page[InvoiceResponse],
)
@limiter.limit("100/minute")
async def search_invoice(
    request: Request,
    business_id: UUID,
    params: Params = Depends(),
    invoice_number: Optional[str] = Query(None, description="Invoice number to search"),
    customer_name: Optional[str] = Query(None, description="Customer name to search"),
    customer_email: Optional[str] = Query(None, description="Customer email to search"),
    issue_date: Optional[str] = Query(None, description="Issue date YYYY-MM-DD"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_dependency),
):

    await business_service.validate_user_owns_business(business_id=business_id, db=db, owner_id=current_user.id)

    query = invoice_service.search_invoice(
        invoice_number=invoice_number,
        customer_name=customer_name,
        customer_email=customer_email,
        issue_date=issue_date,
        business_id=business_id,
        db=db,
    )

    return paginate(query, params)


@router.get(
    "/{business_id}/{invoice_id}",
    status_code=status.HTTP_200_OK,
    response_model=InvoiceResponse,
)
@limiter.limit("100/minute")
async def get_invoice(
    request: Request,
    business_id: UUID,
    invoice_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_dependency),
):
    await business_service.validate_user_owns_business(business_id=business_id, db=db, owner_id=current_user.id)
    return invoice_service.get_invoice(id=invoice_id, business_id=business_id, db=db)


@router.get(
    "/{business_id}",
    status_code=status.HTTP_200_OK,
    response_model=Page[InvoiceResponse],
)
@limiter.limit("100/minute")
async def get_invoices(
    request: Request,
    business_id: UUID,
    params: Params = Depends(),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_dependency),
):
    await business_service.validate_user_owns_business(business_id=business_id, db=db, owner_id=current_user.id)

    query = invoice_service.get_invoices_for_business(business_id=business_id, db=db)
    return paginate(query, params)


@router.put(
    "/{business_id}/{invoice_id}",
    status_code=status.HTTP_200_OK,
    response_model=InvoiceResponse,
)
@limiter.limit("20/minute")
async def update_invoice(
    request: Request,
    invoice_data: InvoiceUpdate,
    business_id: UUID,
    invoice_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_dependency),
):
    await business_service.validate_user_owns_business(business_id=business_id, db=db, owner_id=current_user.id)
    return invoice_service.update_invoice(
        id=invoice_id,
        business_id=business_id,
        db=db,
        invoice_data=invoice_data.model_dump(exclude_unset=True, mode="json"),
    )


@router.delete("/{business_id}/{invoice_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("5/minute")
async def delete_invoice(
    request: Request,
    business_id: UUID,
    invoice_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_dependency),
):
    await business_service.validate_user_owns_business(business_id=business_id, db=db, owner_id=current_user.id)
    return invoice_service.delete_invoice(id=invoice_id, business_id=business_id, db=db)
