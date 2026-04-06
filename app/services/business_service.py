import json
from uuid import UUID
from fastapi import HTTPException, Response, status
from sqlalchemy import exists
from sqlalchemy.orm import Session
from app.core.messages import BUSINESS_NOT_FOUND, NO_BUSINESSES_FOUND, USER_UNAUTHORIZED
from app.db.models.business import Business
from app.core.logger_instance import fastapi_logger as logger
from app.core.redis import redis_client

from app.helpers.orm_to_json import business_to_json
from app.helpers.sentry_helpers.sentry_business_helper import (
    attach_business_full_context,
    attach_business_partial_context,
)


class BusinessService:
    def create_business(self, db: Session, business_data: dict, owner_id: UUID):
        logger.info("Creating Business", owner_id=owner_id)
        business = Business(**business_data, owner_id=owner_id)

        attach_business_partial_context(business)
        db.add(business)
        db.commit()
        db.refresh(business)
        attach_business_full_context(business)

        logger.info("Business Created", business_id=str(business.id))
        return business

    async def validate_user_owns_business(
        self, db: Session, business_id: UUID, owner_id: UUID
    ):
        redis_key = f"business_access:{owner_id}:{business_id}"
        redis_check = await redis_client.get(redis_key)

        if redis_check is not None:
            if redis_check == "1":
                logger.info(
                    "Returning Cached Response for User-Business Validation Lookup"
                )
                return True

            logger.warning(
                "User Unauthorized",
                owner_id=str(owner_id),
                business_id=str(business_id),
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail=USER_UNAUTHORIZED
            )

        db_lookup = db.query(
            exists().where(Business.id == business_id, Business.owner_id == owner_id)
        ).scalar()

        if not db_lookup:
            logger.warning(
                "User Unauthorized",
                owner_id=str(owner_id),
                business_id=str(business_id),
            )

            await redis_client.setex(redis_key, 300, "0")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail=USER_UNAUTHORIZED
            )

        await redis_client.setex(redis_key, 600, "1")

        return True

    async def get_business(self, id: UUID, db: Session, owner_id: UUID):
        redis_key = f"business:{id}"
        redis_check = await redis_client.get(redis_key)
        if redis_check is not None:
            business = json.loads(redis_check)

            if business["owner_id"] != str(owner_id):
                logger.warning(
                    "User Unauthorized",
                    owner_id=str(owner_id),
                    business_id=str(id),
                )
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED, detail=USER_UNAUTHORIZED
                )

            logger.info(
                "Returning Cached Business Data",
                business_id=str(id),
                owner_id=str(owner_id),
            )
            return business

        logger.info("Fetching Business", business_id=str(id))
        business = db.query(Business).filter_by(id=id).first()

        if not business:
            logger.warning("Business Not Found", business_id=str(id))
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=BUSINESS_NOT_FOUND
            )

        if business.owner_id != owner_id:
            logger.warning(
                "User Unauthorized",
                owner_id=str(owner_id),
                business_id=str(business.id),
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail=USER_UNAUTHORIZED
            )

        business_data = business_to_json(business)

        await redis_client.setex(redis_key, 3600, json.dumps(business_data))

        return business_data

    def get_businesses(self, owner_id: UUID, db: Session):
        logger.info("Fetching Businesses", owner_id=str(owner_id))
        businesses = (
            db.query(Business)
            .filter(Business.owner_id == owner_id)
            .order_by(Business.created_at.desc())
        )
        if not businesses:
            logger.warning("No Businesses Found", owner_id=str(owner_id))
            raise HTTPException(
                status_code=status.HTTP_204_NO_CONTENT, detail=NO_BUSINESSES_FOUND
            )
        return businesses

    async def update_business(
        self, id: UUID, owner_id: UUID, db: Session, business_data: dict
    ):
        logger.info("Updating Business", business_id=str(id), owner_id=str(owner_id))
        business = (
            db.query(Business)
            .filter(Business.id == id, Business.owner_id == owner_id)
            .first()
        )
        if not business:
            logger.warning(
                "Business Not Found", business_id=str(id), owner_id=str(owner_id)
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=BUSINESS_NOT_FOUND
            )

        for key, value in business_data.items():
            setattr(business, key, value)

        attach_business_partial_context(business)
        db.commit()
        db.refresh(business)
        attach_business_full_context(business)

        business_redis_key = f"business:{id}"
        business_access_redis_key = f"business_access:{owner_id}:{id}"

        deleted_count = await redis_client.delete(
            business_redis_key, business_access_redis_key
        )
        if deleted_count:
            logger.info("Deleted Business Data From Cache", business_id=str(id))

        logger.info("Business Updated", business_id=str(id), owner_id=str(owner_id))

        return business

    async def delete_business(self, id: UUID, owner_id: UUID, db: Session):
        logger.info("Deleting Business", business_id=str(id), owner_id=str(owner_id))
        business = (
            db.query(Business)
            .filter(Business.id == id, Business.owner_id == owner_id)
            .first()
        )
        if not business:
            logger.warning(
                "Business Not Found", business_id=str(id), owner_id=str(owner_id)
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=BUSINESS_NOT_FOUND
            )
        attach_business_full_context(business)
        db.delete(business)
        db.commit()

        business_redis_key = f"business:{id}"
        business_access_redis_key = f"business_access:{owner_id}:{id}"

        deleted_count = await redis_client.delete(
            business_redis_key, business_access_redis_key
        )
        if deleted_count:
            logger.info("Deleted Business Cache", business_id=str(id))

        logger.info("Business Deleted", business_id=str(id), owner_id=str(owner_id))
        return Response(status_code=status.HTTP_204_NO_CONTENT)
