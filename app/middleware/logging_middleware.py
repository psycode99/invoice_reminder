import uuid
from fastapi import Request
from loguru import logger
from sentry_sdk import configure_scope

async def logging_middleware(request: Request, call_next):
    request_id = str(uuid.uuid4())

    request.state.request_id = request_id

    with configure_scope() as scope:
        scope.set_tag("request_id", request_id)

    with logger.contextualize(
        request_id=request_id,
        method=request.method,
        path=request.url.path,
    ):
        logger.info("Incoming request")

        response = await call_next(request)

        logger.info("Request completed", status_code=response.status_code)

        return response
