from time import time

from fastapi import HTTPException, Request, status
import hashlib
import json
from app.core.logger_instance import fastapi_logger as logger
from app.core.messages import (
    IDEMPOTENCY_KEY_REQUIRED,
    PAYLOAD_MISMATCH,
    PROCESS_ALREADY_EXIST,
)
from redis.asyncio import Redis


async def idempotency_checker(request: Request, redis: Redis, user_id):
    key = request.headers.get("Idempotency-Key")

    if not key:
        logger.warning("Idempotency Key Not Found", user_id=str(user_id))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=IDEMPOTENCY_KEY_REQUIRED
        )

    redis_key = f"Idempotent:{user_id}:{key}"

    req_body = await request.body()
    hashed_body = hashlib.sha256(req_body).hexdigest()

    cached = await redis.get(redis_key)

    if cached:
        data = json.loads(cached)

        if data["payload_hash"] != hashed_body:
            logger.warning(
                "payload hash mismatch",
                user_id=str(user_id),
                redis_key=str(redis_key),
                payload=str(hashed_body),
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=PAYLOAD_MISMATCH
            )

        if data["status"] == "completed":
            logger.info("Returning Cached Response", user_id=str(user_id))
            return {"status": "cached", "response": data["response"]}

        if data["status"] == "processing":
            logger.warning(
                "Task is still processing",
                user_id=str(user_id),
                redis_key=str(redis_key),
                payload=str(hashed_body),
            )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail=PROCESS_ALREADY_EXIST
            )

    await redis.set(
        redis_key,
        json.dumps(
            {
                "status": "processing",
                "payload_hash": hashed_body,
            }
        ),
        ex=300,
    )

    return {"status": "new", "redis_key": redis_key, "hashed_body": hashed_body}
