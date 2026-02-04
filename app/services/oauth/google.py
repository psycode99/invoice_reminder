from fastapi import Request
from app.services.oauth.base import OauthProvider
from authlib.integrations.starlette_client import OAuth
from app.core.config import settings

google_oauth = OAuth()

google_oauth.register(
    name='google',
    client_id=settings.google_client_id,
    client_secret=settings.google_client_secret,
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile'
    }
)

class GoogleProvider(OauthProvider):
    
    async def get_auth_url(self, request: Request, redirect_uri):
        return await google_oauth.google.authorize_redirect(request, redirect_uri)
    
    async def fetch_user(self, request: Request):
        provider_name = "google"
        token = await google_oauth.google.authorize_access_token(request)
        provider_resp: dict = token.get("userinfo")
        user_info = {
            "email": provider_resp.get("email"),
            "email_verified": provider_resp.get("email_verified"),
            "auth_provider": provider_name,
            "provider_user_id": provider_resp.get("sub"),
            "full_name": provider_resp.get("name"),
            "avatar_url": provider_resp.get("picture")
        }

        return user_info