from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Request, status
from app.api.v1.dependencies import get_db
from app.core.security import encode_business_state
from app.services.accounting_integrations.qbo_integration import QuickBooksOnlineIntegration
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.services.accounting_integrations_service import AccountingIntegrationService

integration_service = AccountingIntegrationService(
    integrations={"qbo": QuickBooksOnlineIntegration()}
)
router = APIRouter(prefix="/v1/integrations", tags=["Integrations"])


@router.get("/{integration_name}/connect", status_code=status.HTTP_202_ACCEPTED)
def connect_account(integration_name: str, business_id: UUID):
    integrations = [i for i in integration_service.integrations.keys()]

    if integration_name not in integrations:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    
    business_state = encode_business_state(str(business_id))

    return RedirectResponse(
        url=integration_service.get_auth_url(integration_name=integration_name, state=business_state).get(
            "url"
        )
    )


@router.get("/{integration_name}/callback", status_code=status.HTTP_200_OK)
def handle_callback(
    request: Request, integration_name: str, db: Session = Depends(get_db)
):
    return integration_service.handle_callback(
        request=request, integration_name=integration_name, db=db
    )
