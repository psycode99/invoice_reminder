from typing import List
from uuid import UUID
from fastapi import HTTPException, Response, status
from sqlalchemy.orm import Session
from app.core.messages import BUSINESS_NOT_FOUND, NO_BUSINESSES_FOUND, USER_UNAUTHORIZED
from app.db.models.business import Business
from sqlalchemy import update


class BusinessService:
    def create_business(self, db: Session, business_data: dict, owner_id: UUID):
        business = Business(**business_data, owner_id=owner_id)
        db.add(business)
        db.commit()
        db.refresh(business)
        return business

    def get_business(self, id: UUID, db: Session, owner_id: UUID):
        business = db.query(Business).filter_by(id=id).first()
        if not business:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=BUSINESS_NOT_FOUND
            )
        if business.owner_id != owner_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail=USER_UNAUTHORIZED
            )
        return business

    def get_businesses(self, owner_id: UUID, db: Session):
        businesses = db.query(Business).filter_by(owner_id=owner_id).all()
        if not businesses:
            raise HTTPException(
                status_code=status.HTTP_204_NO_CONTENT, detail=NO_BUSINESSES_FOUND
            )
        return businesses

    def update_business(
        self, id: UUID, owner_id: UUID, db: Session, business_data: dict
    ):
        business = db.query(Business).filter(id=id, owner_id=owner_id).first()
        if not business:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=BUSINESS_NOT_FOUND
            )

        for key, value in business_data.items():
            setattr(business, key, value)

        db.commit()
        db.refresh(business)
        return business

    def delete_business(self, id: UUID, owner_id: UUID, db: Session):
        business = db.query(Business).filter(id=id, owner_id=owner_id).first()
        if not business:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=BUSINESS_NOT_FOUND
            )
        db.delete(business)
        db.commit()
        return Response(status_code=status.HTTP_204_NO_CONTENT)
