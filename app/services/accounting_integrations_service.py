from fastapi import Request
from sqlalchemy.orm import Session

from app.services.accounting_integrations.base import AccountingIntegrations


class AccountingIntegrationService:
    def __init__(self, integrations: dict[str, AccountingIntegrations]):
        self.integrations = integrations

    def get_auth_url(self, integration_name: str, state):
        service = self.integrations.get(integration_name)
        return service.get_auth_url(state=state)

    def handle_callback(self, integration_name: str, request: Request, db: Session):
        service = self.integrations.get(integration_name)
        return service.handle_callback(request=request, db=db)
