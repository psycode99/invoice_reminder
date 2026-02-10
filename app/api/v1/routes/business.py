from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, status
from app.api.v1.dependencies import get_db
from app.schemas.business_schema import BusinessCreate, BusinessResponse, BusinessUpdate
from sqlalchemy.orm import Session
from app.core.security import get_current_user_dependency
from app.services.business_service import BusinessService


router = APIRouter(prefix="/v1/businesses", tags=["Business"])
business_service = BusinessService()


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=BusinessResponse)
def create_business(
    business_data: BusinessCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_dependency),
):
    return business_service.create_business(
        db=db, business_data=business_data.model_dump(mode="json"), owner_id=current_user.id
    )


@router.get("/{id}", status_code=status.HTTP_200_OK, response_model=BusinessResponse)
def get_business(
    id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_dependency),
):

    return business_service.get_business(id=id, db=db, owner_id=current_user.id)


@router.get("/", status_code=status.HTTP_200_OK, response_model=List[BusinessResponse])
def get_businesses(
    db: Session = Depends(get_db), current_user=Depends(get_current_user_dependency)
):
    return business_service.get_businesses(owner_id=current_user.id, db=db)


@router.put("/{id}", status_code=status.HTTP_200_OK, response_model=BusinessResponse)
def update_business(
    business_data: BusinessUpdate,
    id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_dependency),
):
    return business_service.update_business(
        id=id, owner_id=current_user.id, db=db, business_data=business_data.model_dump(exclude_unset=True, mode="json")
    )


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_business(
    id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_dependency),
):
    return business_service.delete_business(id=id, owner_id=current_user.id, db=db)
