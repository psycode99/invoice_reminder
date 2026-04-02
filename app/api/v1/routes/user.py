from uuid import UUID
from fastapi import Depends, APIRouter, Request, status
from app.services.user_service import UserService
from app.api.v1.dependencies import get_db
from app.core.security import get_current_user_dependency
from sqlalchemy.orm import Session
from app.schemas.user_schema import UserResponse
from app.main import limiter


router = APIRouter(prefix="/v1/users", tags=["User"])
user_service = UserService()


@router.get("/", status_code=status.HTTP_200_OK, response_model=UserResponse)
@limiter.limit("100/minute")
def get_user(
    request: Request,
    current_user=Depends(get_current_user_dependency),
    db: Session = Depends(get_db),
):

    return user_service.get_user(db=db, id=current_user.id)


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("5/minute")
def delete_user(
    request: Request,
    id: UUID = id,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_dependency),
):

    return user_service.delete_user(db=db, id=id, current_user_id=current_user.id)
