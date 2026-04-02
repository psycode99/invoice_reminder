from uuid import UUID
from fastapi import HTTPException, Request, status
from sqlalchemy.orm import Session
from loguru import logger
from app.core.messages import (
    INTEGRATION_CONNECTION_ALREADY_EXISTS,
    INTEGRATION_NOT_FOUND,
)
from app.services.accounting_integrations.base import AccountingIntegrations
from app.db.models import AccountingIntegration
from app.core.logger_instance import fastapi_logger as logger

class AccountingIntegrationService:
    def __init__(self, integrations: dict[str, AccountingIntegrations]):
        self.integrations = integrations

    def get_auth_url(
        self, integration_name: str, state, business_id: UUID, db: Session
    ):
        integration_exists = (
            db.query(AccountingIntegration)
            .filter(
                AccountingIntegration.business_id == business_id,
                AccountingIntegration.provider == integration_name,
            )
            .first()
        )

        if not integration_exists:
            service = self.integrations.get(integration_name)
            logger.info("Fetching Authorization URL", integration=integration_name)
            url = service.get_auth_url(state=state)
            return {"url": url}

        if integration_exists.connected:
            logger.warning(
                "Accounting Integration Connection Already Exists",
                business_id=str(business_id),
                provider=str(integration_name),
            )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=INTEGRATION_CONNECTION_ALREADY_EXISTS,
            )
        else:
            logger.info(
                "Reconnecting Preexisting Connection",
                business_id=str(business_id),
                provider=str(integration_name),
            )
            integration_exists.connected = True
            db.commit()
            return {"message": "Reconnection Successful"}

    def handle_callback(self, integration_name: str, request: Request, db: Session):
        service = self.integrations.get(integration_name)
        logger.info("Handling Callback For Integration", integration=integration_name)
        return service.handle_callback(request=request, db=db)

    def sync_invoices(
        self,
        integration_name: str,
        business_id: UUID,
        accounting_integration_id: UUID,
        request: Request,
    ):
        service = self.integrations.get(integration_name)
        logger.info(
            "Syncing Invoices",
            integration=integration_name,
            business_id=str(business_id),
            accounting_integration_id=str(accounting_integration_id),
        )
        return service.sync_invoices(
            business_id=business_id,
            accounting_integration_id=accounting_integration_id,
            request=request,
        )

    def webhooks_handler(self, integration_name: str, request: Request):
        service = self.integrations.get(integration_name)
        logger.info("Handling webhooks", integration=integration_name)
        return service.webhooks_handler(request=request)

    def disconnect(self, integration_name: str, business_id: UUID, db: Session):
        integration_exists = (
            db.query(AccountingIntegration)
            .filter(
                AccountingIntegration.business_id == business_id,
                AccountingIntegration.provider == integration_name,
                AccountingIntegration.connected == True,
            )
            .first()
        )

        if not integration_exists:
            logger.warning(
                "Accounting Integration Connection Does Not Exist",
                business_id=str(business_id),
                provider=str(integration_name),
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail=INTEGRATION_NOT_FOUND
            )

        service = self.integrations.get(integration_name)
        logger.info(
            "Disconnecting Integration",
            integration=integration_name,
            business_id=str(business_id),
        )
        return service.disconnect(business_id=business_id, db=db)
