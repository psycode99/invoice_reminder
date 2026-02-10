from fastapi import HTTPException, Response, status
from app.core.messages import USER_NOT_FOUND
from app.db.models.users import User
from sqlalchemy.orm import Session


class UserService():
    async def get_user(self, db: Session,  id: str):
        user = db.query(User).filter_by(id=id).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=USER_NOT_FOUND)
        return user
    
    async def delete_user(self, db: Session, id: str):
        user = db.query(User).filter_by(id=id).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=USER_NOT_FOUND)
        db.delete(user)
        db.commit()
        return Response(status_code=status.HTTP_204_NO_CONTENT)