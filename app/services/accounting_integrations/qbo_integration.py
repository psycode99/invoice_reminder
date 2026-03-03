from datetime import UTC, datetime, timedelta
from uuid import UUID
from fastapi import HTTPException, Request, status
from intuitlib.client import AuthClient
from intuitlib.enums import Scopes
from app.tasks.invoice_sync_tasks import sync_qbo_invoices

from app.core.config import settings
from app.core.messages import MISSING_AUTH_CODE, MISSING_STATE
from app.core.security import decode_business_state
from app.services.accounting_integrations.base import AccountingIntegrations
from sqlalchemy.orm import Session
from app.db.models.accounting_integration import AccountingIntegration


auth_client = AuthClient(
    client_id=settings.qbo_client_id,
    client_secret=settings.qbo_client_secret,
    redirect_uri=settings.qbo_redirect_uri,
    environment=settings.qbo_environment,
)

class QuickBooksOnlineIntegration(AccountingIntegrations):
    def get_auth_url(self, state):
        url = auth_client.get_authorization_url(
            scopes=[Scopes.ACCOUNTING],
            state_token=state
        )
        return {"url": url}

    def handle_callback(self, request: Request, db: Session):
        code = request.query_params.get("code")
        realm_id = request.query_params.get("realmId")
        state = request.query_params.get("state")

        if not code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=MISSING_AUTH_CODE
            )
        
        if not state:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=MISSING_STATE
            )
        
        business_id = decode_business_state(state).get("business_id")

        auth_client.get_bearer_token(auth_code=code)

        access_token = auth_client.access_token
        refresh_token = auth_client.refresh_token
        expires_in = auth_client.expires_in

        integration_data = {
            "business_id": business_id,
            "provider": "qbo",
            "access_token": access_token,
            "refresh_token": refresh_token,
            "company_id": realm_id,
            "expires_at": datetime.now(UTC) + timedelta(seconds=expires_in)
        }

        new_integration = AccountingIntegration(**integration_data)
        db.add(new_integration)
        db.commit()

        return {
            "access_token": access_token,
            "business_id": business_id
        }
    
    def sync_invoices(self, business_id: UUID, accounting_integration_id: UUID):
        sync_qbo_invoices.delay(business_id, accounting_integration_id)
        return {"message": "syncing..."}
