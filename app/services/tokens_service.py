from sqlalchemy.orm import Session
from app.core.messages import REFRESH_TOKEN_NOT_FOUND
from app.core.security import create_refresh_token, decode_jwt, hash_token
from app.db.models.refresh_tokens import RefreshToken
from loguru import logger
from fastapi import HTTPException, status
from datetime import datetime, timezone


class RefreshTokens:
    def store_refresh_token(self, db: Session, refresh_token: str):
        decoded_token = decode_jwt(refresh_token)
        expires_at = datetime.fromtimestamp(decoded_token["exp"], tz=timezone.utc)

        user_id = decoded_token.get("sub")

        logger.info("storing refresh token".title(), user_id=str(user_id))

        token_hash = hash_token(refresh_token)
        token = RefreshToken(
            user_id=user_id, expires_at=expires_at, token_hash=token_hash
        )

        db.add(token)
        db.commit()
        logger.info("Refresh Token Stored".title(), user_id=str(user_id))
        db.refresh(token)

    def get_refresh_token(self, db: Session, refresh_token: str):
        user_id = decode_jwt(refresh_token).get("sub")

        logger.info("Fetching Refresh Token", user_id=str(user_id))

        token_hash = hash_token(refresh_token)
        rf_token = (
            db.query(RefreshToken)
            .filter(
                RefreshToken.user_id == user_id,
                RefreshToken.token_hash == token_hash,
                RefreshToken.revoked == False,
                RefreshToken.expires_at > datetime.now(timezone.utc),
            )
            .first()
        )

        if not rf_token:
            logger.warning("Refresh Token Not Found", user_id=str(user_id))
            raise HTTPException(
                status.HTTP_401_UNAUTHORIZED, detail=REFRESH_TOKEN_NOT_FOUND
            )

        return rf_token

    def revoke_refresh_token(self, db: Session, refresh_token: str):
        user_id = decode_jwt(refresh_token).get("sub")
        logger.info("Revoking Refresh Token", user_id=str(user_id))

        hashed_refresh_token = hash_token(refresh_token)
        rf_token = (
            db.query(RefreshToken)
            .filter(
                RefreshToken.user_id == user_id,
                RefreshToken.token_hash == hashed_refresh_token,
                RefreshToken.revoked == False,
            )
            .first()
        )

        if not rf_token:
            logger.warning("Refresh Token Not Found", user_id=str(user_id))
            raise HTTPException(
                status.HTTP_401_UNAUTHORIZED, detail=REFRESH_TOKEN_NOT_FOUND
            )

        rf_token.revoked = True
        db.commit()
        logger.info("Refresh Token Revoked", user_id=str(user_id))

        db.refresh(rf_token)

    def rotate_refresh_token(self, db: Session, old_refresh_token: str):
        user_id = decode_jwt(old_refresh_token).get("sub")

        logger.info("Rotating Refresh Token", user_id=str(user_id))

        token_hash = hash_token(old_refresh_token)

        rf_token = (
            db.query(RefreshToken)
            .filter(
                RefreshToken.user_id == user_id,
                RefreshToken.token_hash == token_hash,
                RefreshToken.revoked == False,
                RefreshToken.expires_at > datetime.now(timezone.utc),
            )
            .first()
        )

        if not rf_token:
            logger.warning("Refresh Token Not Found", user_id=str(user_id))
            raise HTTPException(
                status.HTTP_401_UNAUTHORIZED,
                detail=REFRESH_TOKEN_NOT_FOUND,
            )

        # Revoke old
        rf_token.revoked = True

        # Create new
        new_refresh_token, expires_in = create_refresh_token(user_id)
        new_hash = hash_token(new_refresh_token)

        new_token = RefreshToken(
            user_id=user_id,
            token_hash=new_hash,
            expires_at=expires_in,
        )

        user_id = new_token.user_id

        rf_token.replaced_by_token = new_token.id
        db.add(new_token)
        db.commit()

        logger.info("Refresh Token Rotated", user_id=str(user_id))
        return new_refresh_token, user_id, expires_in
