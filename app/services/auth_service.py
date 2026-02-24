from fastapi import HTTPException, Request, status

from app.core.security import create_access_token, create_refresh_token, decode_jwt
from app.services.oauth.base import OauthProvider
from app.db.models.users import User
from sqlalchemy.orm import Session
from loguru import logger


class AuthService:
    def __init__(self, providers: dict[str, OauthProvider]):
        self.providers = providers

    async def login_redirect(self, provider_name: str, request: Request):
        logger.info("Logging in User", provider_name=provider_name)

        provider = self.providers.get(provider_name)
        redirect_uri = request.url_for("oauth_callback", provider=provider_name)
        return await provider.get_auth_url(request=request, redirect_uri=redirect_uri)

    async def handle_callback(self, provider_name: str, request: Request, db: Session):
        provider = self.providers.get(provider_name)
        provider_resp = await provider.fetch_user(request=request)

        user = (
            db.query(User)
            .filter_by(
                auth_provider=provider_resp.get("auth_provider"),
                provider_user_id=provider_resp.get("provider_user_id"),
            )
            .first()
        )

        if not user:
            user = User(**provider_resp)
            db.add(user)
            db.commit()
            db.refresh(user)
            logger.info("New User Created", user_id=str(user.id))

        access_token = create_access_token(user.id)
        refresh_token, expires_in = create_refresh_token(user.id)
        logger.info("User Logged In", user_id=str(user.id))
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "refresh_token_exp": expires_in,
        }

    def get_current_user(self, token, db: Session):
        payload = decode_jwt(token)
        user_id = str(payload.get("sub"))
        user = db.query(User).filter_by(id=user_id).first()
        if not user:
            logger.warning("User Not Found", user_id=str(user_id))
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User Not Found"
            )
        return user
