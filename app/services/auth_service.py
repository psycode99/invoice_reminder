from fastapi import HTTPException, Request, status

from app.core.security import create_access_token, decode_jwt
from app.services.oauth.base import OauthProvider
from app.db.models.users import User
from sqlalchemy.orm import Session


class AuthService():
    def __init__(self, providers: dict[str, OauthProvider]):
        self.providers = providers

    async def login_redirect(self, provider_name: str, request: Request):
        provider = self.providers.get(provider_name)
        redirect_uri = request.url_for("oauth_callback", provider=provider_name)
        return await provider.get_auth_url(request=request, redirect_uri=redirect_uri)
    
    async def handle_callback(self, provider_name: str, request: Request, db: Session):
        provider = self.providers.get(provider_name)
        provider_resp =  await provider.fetch_user(request=request)

        user = db.query(User).filter_by(auth_provider=provider_resp.get("auth_provider"),
                                        provider_user_id=provider_resp.get("provider_user_id")).first()
        
        if not user:
            user = User(**provider_resp)
            db.add(user)
            db.commit()
            db.refresh(user)
        access_token = create_access_token(user.id)
        return {"access_token": access_token, "type": "bearer"}
        

    def get_current_user(self, token, db: Session):
        payload = decode_jwt(token)
        user_id = str(payload.get('sub'))
        user = db.query(User).filter_by(id=user_id).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User Not Found")
        return user

        