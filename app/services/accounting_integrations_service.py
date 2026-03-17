from uuid import UUID
from fastapi import Request
from sqlalchemy.orm import Session
from loguru import logger
from app.services.accounting_integrations.base import AccountingIntegrations


class AccountingIntegrationService:
    def __init__(self, integrations: dict[str, AccountingIntegrations]):
        self.integrations = integrations

    def get_auth_url(self, integration_name: str, state):
        service = self.integrations.get(integration_name)
        logger.info("Fetching Authorization URL", integration=integration_name)
        return service.get_auth_url(state=state)

    def handle_callback(self, integration_name: str, request: Request, db: Session):
        service = self.integrations.get(integration_name)
        logger.info("Handling Callback For Integration", integration=integration_name)
        return service.handle_callback(request=request, db=db)
    
    def sync_invoices(self, integration_name: str, business_id: UUID, accounting_integration_id: UUID, request: Request):
        service = self.integrations.get(integration_name)
        logger.info("Syncing Invoices")
        return service.sync_invoices(business_id=business_id, accounting_integration_id=accounting_integration_id)
    
    def webhooks_handler(self, integration_name: str, request: Request):
        service = self.integrations.get(integration_name)
        logger.info("Handling webhooks", integration=integration_name)
        return service.webhooks_handler(request=request)
