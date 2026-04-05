from app.db.session import SessionLocal
from app.core.redis import redis_client

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_redis():
    return redis_client