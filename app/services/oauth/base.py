from abc import ABC, abstractmethod
from fastapi import Request

class OauthProvider(ABC):
    @abstractmethod
    async def get_auth_url(self, request: Request, redirect_uri) -> str:
        pass

    @abstractmethod
    async def fetch_user(self, request: Request) -> dict:
        pass