from uuid import UUID
from fastapi import HTTPException, Response, status
from sqlalchemy.orm import Session
from app.core.messages import BUSINESS_NOT_FOUND, NO_BUSINESSES_FOUND, USER_UNAUTHORIZED
from app.db.models.business import Business
from loguru import logger


class BusinessService:
    def create_business(self, db: Session, business_data: dict, owner_id: UUID):
        logger.info("Creating Business", owner_id=owner_id)
        business = Business(**business_data, owner_id=owner_id)
        db.add(business)
        db.commit()
        db.refresh(business)
        logger.info("Business Created", business_id=str(business.id))
        return business

    def get_business(self, id: UUID, db: Session, owner_id: UUID):
        logger.info("Fetching Business", business_id=str(id))
        business = db.query(Business).filter_by(id=id).first()

        if business.owner_id != owner_id:
            logger.warning(
                "User Unauthorized",
                owner_id=str(owner_id),
                business_id=str(business.id),
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail=USER_UNAUTHORIZED
            )
    
        if not business:
            logger.warning("Business Not Found", business_id=str(id))
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=BUSINESS_NOT_FOUND
            )
 
        return business

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

    def update_business(
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

        db.commit()
        db.refresh(business)
        logger.info("Business Updated", business_id=str(id), owner_id=str(owner_id))
        return business

    def delete_business(self, id: UUID, owner_id: UUID, db: Session):
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
        db.delete(business)
        db.commit()
        logger.info("Business Deleted", business_id=str(id), owner_id=str(owner_id))
        return Response(status_code=status.HTTP_204_NO_CONTENT)
