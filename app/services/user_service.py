from uuid import UUID
from fastapi import HTTPException, Response, status
from app.core.messages import USER_NOT_FOUND, USER_UNAUTHORIZED
from app.db.models.users import User
from sqlalchemy.orm import Session
from loguru import logger

class UserService():
    def get_user(self, db: Session,  id: UUID):
        logger.info("Fetching User", user_id=str(id))

        user = db.query(User).filter_by(id=id).first()
        if not user:
            logger.warning("User Not Found", user_id=str(id))
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=USER_NOT_FOUND)
        return user
    
    def delete_user(self, db: Session, id: UUID, current_user_id: UUID):
        logger.info("Deleting User", user_id=str(id))

        user = db.query(User).filter_by(id=id).first()
        if not user:
            logger.warning("User Not Found", user_id=str(id))
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=USER_NOT_FOUND)
        
        if current_user_id != id:
            logger.warning("User Not Authorized", user_to_del_id=str(id), curr_user_id=str(current_user_id))
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail=USER_UNAUTHORIZED
            )
        
        db.delete(user)
        db.commit()

        logger.info("User Deleted", user_id=str(id))
        return Response(status_code=status.HTTP_204_NO_CONTENT)