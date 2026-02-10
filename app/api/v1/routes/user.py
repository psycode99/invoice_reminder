from fastapi import Depends, APIRouter, HTTPException, status
from app.core.messages import USER_UNAUTHORIZED
from app.services.user_service import UserService
from app.api.v1.dependencies import get_db
from app.core.security import get_current_user_dependency
from sqlalchemy.orm import Session
from app.schemas.user_schema import UserResponse

router = APIRouter(prefix='/v1/users', tags=['User'])
user_service = UserService()

@router.get("/", status_code=status.HTTP_200_OK, response_model=UserResponse)
async def get_user(current_user = Depends(get_current_user_dependency), db: Session = Depends(get_db)):
    user_id = current_user.id
    return await user_service.get_user(db=db, id=user_id)


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(id: str = id, db: Session = Depends(get_db), current_user = Depends(get_current_user_dependency)):
    if current_user.id != id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=USER_UNAUTHORIZED)
    return await user_service.delete_user(db=db, id=id)