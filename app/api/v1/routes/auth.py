from datetime import datetime, timezone
from fastapi import Cookie, HTTPException, Request, status, APIRouter, Depends, Response
from app.core.messages import REFRESH_TOKEN_NOT_FOUND
from app.core.security import create_access_token
from app.services.auth_service import AuthService
from app.services.oauth.google import GoogleProvider
from app.api.v1.dependencies import get_db
from sqlalchemy.orm import Session
from app.core.config import settings

from app.services.tokens_service import RefreshTokens

router = APIRouter(prefix="/v1/auth", tags=["Auth"])
auth_service = AuthService(providers={"google": GoogleProvider()})
token_service = RefreshTokens()


@router.get("/{provider}/login", status_code=status.HTTP_200_OK, name="oauth_login")
async def oauth_login(request: Request, provider: str):
    return await auth_service.login_redirect(provider_name=provider, request=request)


@router.get(
    "/{provider}/callback", status_code=status.HTTP_200_OK, name="oauth_callback"
)
async def oauth_callback(
    provider: str, request: Request, response: Response, db: Session = Depends(get_db)
):
    tokens: dict = await auth_service.handle_callback(
        provider_name=provider, request=request, db=db
    )

    access_token = tokens.get("access_token")
    refresh_token = tokens.get("refresh_token")
    refresh_token_exp = tokens.get("refresh_token_exp")
    max_age = int((refresh_token_exp - datetime.now(timezone.utc)).total_seconds())

    token_service.store_refresh_token(db=db, refresh_token=refresh_token)

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=settings.prod,  # True in production (HTTPS)
        samesite="lax",
        max_age=max_age,
    )

    return {"access_token": access_token, "type": "bearer"}


@router.post("/refresh", status_code=status.HTTP_200_OK)
def refresh_token(
    response: Response, refresh_token: str = Cookie(None), db: Session = Depends(get_db)
):
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=REFRESH_TOKEN_NOT_FOUND
        )

    token_service.get_refresh_token(db=db, refresh_token=refresh_token)

    new_rf_token, user_id, expires_in = token_service.rotate_refresh_token(
        db=db, old_refresh_token=refresh_token
    )
    max_age = max(0, int((expires_in - datetime.now(timezone.utc)).total_seconds()))

    response.set_cookie(
        key="refresh_token",
        value=new_rf_token,
        httponly=True,
        secure=settings.prod,  # True in production (HTTPS)
        samesite="lax",
        max_age=max_age,
    )

    new_access_token = create_access_token(user_id)

    return {"access_token": new_access_token, "type": "bearer"}
