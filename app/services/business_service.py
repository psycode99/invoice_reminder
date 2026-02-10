from typing import List
from fastapi import HTTPException, Response, status
from sqlalchemy.orm import Session
from app.core.messages import BUSINESS_NOT_FOUND, NO_BUSINESSES_FOUND
from app.db.models.business import Business
from sqlalchemy import update


class BusinessService():
    def create_business(self, db: Session, business_data: dict):
        business = Business(**business_data)
        db.add(business)
        db.commit()

    def get_business(self, id: str, db: Session):
        business = db.query(Business).filter_by(id).first()
        if not business:
            raise HTTPException(status_codde=status.HTTP_404_NOT_FOUND, detail=BUSINESS_NOT_FOUND)
        return business
    
    def get_businesses(self, user_id: str, db: Session):
        businesses = db.query(Business).filter_by(owner_id=user_id).all()
        if not businesses:
            raise HTTPException(status_code=status.HTTP_204_NO_CONTENT, detail=NO_BUSINESSES_FOUND)
        return businesses
    
    def update_business(self, id: str, user_id: str, db: Session, business_data: dict):
        business = db.query(Business).filter(id=id, owner_id=user_id).first()
        if not business:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=BUSINESS_NOT_FOUND)
        
        for key, value in business_data.items():
            setattr(business, key, value)
            
        db.commit()
        db.refresh(business)
        return business
    
    def delete_business(self, id: str, user_id: str, db: Session):
        business = db.query(Business).filter(id=id, owner_id=user_id).first()
        if not business:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=BUSINESS_NOT_FOUND)
        db.delete(business)
        db.commit()
        return Response(status_code=status.HTTP_204_NO_CONTENT)
