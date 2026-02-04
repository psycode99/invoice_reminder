from fastapi import Request, status, APIRouter, Depends
from app.services.auth_service import AuthService
from app.services.oauth.google import GoogleProvider
from app.api.v1.dependencies import get_db
from sqlalchemy.orm import Session

router = APIRouter(prefix='/v1/auth', tags=['Auth'])
auth_service = AuthService(providers={
    "google": GoogleProvider()
})

@router.get('/{provider}/login', status_code=status.HTTP_200_OK, name="oauth_login")
async def oauth_login(request: Request, provider: str):
    return await auth_service.login_redirect(provider_name=provider, request=request)

@router.get('/{provider}/callback', status_code=status.HTTP_200_OK, name="oauth_callback")
async def oauth_callback(provider: str, request: Request, db:Session = Depends(get_db)):
    return await auth_service.handle_callback(provider_name=provider, request=request, db=db)