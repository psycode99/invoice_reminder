from abc import abstractmethod, ABC
from fastapi import Request
from sqlalchemy.orm import Session


class AccountingIntegrations(ABC):

    @abstractmethod
    def get_auth_url(self, state: str):
        pass

    @abstractmethod
    def handle_callback(self, request: Request, db: Session):
        pass
