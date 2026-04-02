from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Header, Request, status, Depends
from app.api.v1.dependencies import get_db
from app.core.messages import INTEGRATION_NOT_FOUND, MISSING_SIGNATURE
from app.core.security import encode_business_state, get_current_user_dependency
from app.services.accounting_integrations.qbo_integration import (
    QuickBooksOnlineIntegration,
)
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.services.accounting_integrations_service import AccountingIntegrationService
from app.services.business_service import BusinessService
from app.main import limiter

integration_service = AccountingIntegrationService(
    integrations={"qbo": QuickBooksOnlineIntegration()}
)
business_service = BusinessService()
router = APIRouter(prefix="/v1/integrations", tags=["Integrations"])


def check_integrations(integration_name):
    integrations = [i for i in integration_service.integrations.keys()]

    if integration_name not in integrations:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=INTEGRATION_NOT_FOUND
        )


@router.get("/{integration_name}/connect", status_code=status.HTTP_202_ACCEPTED)
@limiter.limit("10/minute")
def connect_account(
    request: Request,
    integration_name: str,
    business_id: UUID,
    db: Session = Depends(get_db),
):
    check_integrations(integration_name)

    business_state = encode_business_state(str(business_id))
    resp = integration_service.get_auth_url(
        integration_name=integration_name,
        state=business_state,
        business_id=business_id,
        db=db,
    )

    if "url" in resp:
        return RedirectResponse(resp.get("url"))
    return resp


@router.get("/{integration_name}/callback", status_code=status.HTTP_200_OK)
def handle_callback(
    request: Request, integration_name: str, db: Session = Depends(get_db)
):
    return integration_service.handle_callback(
        request=request, integration_name=integration_name, db=db
    )


@router.get("/{integration_name}/sync_invoices", status_code=status.HTTP_200_OK)
@limiter.limit("10/minute")
def sync_invoices(
    request: Request,
    integration_name: str,
    business_id: UUID,
    accounting_integration_id: UUID,
    db: Session = Depends(get_db),
    # current_user=Depends(get_current_user_dependency),
):
    check_integrations(integration_name)

    # business_service.get_business(id=business_id, db=db, owner_id=current_user.id)
    return integration_service.sync_invoices(
        integration_name=integration_name,
        business_id=business_id,
        accounting_integration_id=accounting_integration_id,
        request=request,
    )


@router.post("/{integration_name}/wh/notifications", status_code=status.HTTP_200_OK)
async def webhooks_handler(
    integration_name: str,
    request: Request,
):
    check_integrations(integration_name)

    return await integration_service.webhooks_handler(
        integration_name=integration_name, request=request
    )


@router.get("/{integration_name}/disconnect", status_code=status.HTTP_200_OK)
@limiter.limit("5/minute")
def disconnect(
    request: Request,
    integration_name: str,
    business_id: UUID,
    db: Session = Depends(get_db),
):
    check_integrations(integration_name)

    return integration_service.disconnect(
        integration_name=integration_name, business_id=business_id, db=db
    )
