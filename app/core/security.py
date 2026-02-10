from datetime import datetime, timezone, timedelta
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


from app.api.v1.dependencies import get_db
from app.services.oauth.google import GoogleProvider

SECRET_KEY = settings.secret_key
ALGORITHM = settings.algorithm
EXPIRATION_MINUTES = settings.expiration_minutes


def create_access_token(id: str):
    expires_in = datetime.now(timezone.utc) + timedelta(minutes=EXPIRATION_MINUTES)
    to_encode = {"exp": expires_in, "sub": str(id)}
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, ALGORITHM)
    return encoded_jwt


def decode_jwt(encoded_jwt: dict) -> dict:
    try:
        decoded_jwt = jwt.decode(encoded_jwt, SECRET_KEY, algorithms=[ALGORITHM])
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Token"
        )
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has Expired"
        )
    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Token"
        )
    except InvalidSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Signature on Token",
        )
    except DecodeError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Error Decoding Token"
        )
    return decoded_jwt


def get_current_user_dependency(token, db: Session = Depends(get_db)):
    from app.services.auth_service import AuthService

    auth_service = AuthService(providers={"google": GoogleProvider()})

    return auth_service.get_current_user(token=token, db=db)
