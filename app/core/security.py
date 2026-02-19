from datetime import datetime, timezone, timedelta
from uuid import UUID
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException, status
from app.core.config import settings
import jwt
from jwt import (
    ExpiredSignatureError,
    InvalidSignatureError,
    DecodeError,
    InvalidTokenError,
)

from loguru import logger
from app.api.v1.dependencies import get_db
from app.services.oauth.google import GoogleProvider

SECRET_KEY = settings.secret_key
ALGORITHM = settings.algorithm
EXPIRATION_MINUTES = settings.expiration_minutes

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def create_access_token(id: UUID):
    logger.info("Creating JWT", user_id=str(id))

    expires_in = datetime.now(timezone.utc) + timedelta(minutes=EXPIRATION_MINUTES)
    to_encode = {"exp": expires_in, "sub": str(id)}
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, ALGORITHM)

    logger.info("JWT Created", user_id=str(id))
    return encoded_jwt


def decode_jwt(encoded_jwt: str) -> dict:
    try:
        decoded_jwt = jwt.decode(encoded_jwt, SECRET_KEY, algorithms=[ALGORITHM])
    except ExpiredSignatureError:
        logger.exception("Token Has Expired")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has Expired"
        )
    except InvalidTokenError:
        logger.exception("Invalid Token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Token"
        )
    except InvalidSignatureError:
        logger.exception("Invalid Token Signature")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Signature on Token",
        )
    except DecodeError:
        logger.exception("Error Decoding Token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Error Decoding Token"
        )
    return decoded_jwt


def get_current_user_dependency(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    from app.services.auth_service import AuthService

    auth_service = AuthService(providers={"google": GoogleProvider()})

    return auth_service.get_current_user(token=token, db=db)
