from app.middleware.logging_middleware import logging_middleware
from fastapi import FastAPI, Request
from starlette.middleware.sessions import SessionMiddleware
from fastapi_pagination import add_pagination
from app.core.logging import setup_logger
import sentry_sdk
from sentry_sdk.integrations.asgi import SentryAsgiMiddleware
from app.core.config import settings
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi import Limiter
from fastapi.responses import JSONResponse

from app.middleware.rate_limiting_middleware import attach_user

logger = setup_logger()

sentry_sdk.init(
    dsn=settings.sentry_dsn,
    send_default_pii=True,
)

app = FastAPI()
app.middleware("http")(logging_middleware)
app.middleware("http")(attach_user)
app.add_middleware(SessionMiddleware, secret_key=settings.session_middleware_key)
app.add_middleware(SentryAsgiMiddleware)


def key_func(request: Request):
    user_id = getattr(request.state, "user_id", None)
    if user_id:
        return f"user_id:{user_id}"
    return f"ip:{get_remote_address(request)}"


limiter = Limiter(key_func=key_func, storage_uri=settings.redis_backend)

app.state.limiter = limiter


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(status_code=429, content={"detail": "Rate Limit Exceeded"})


@app.get("/")
@limiter.limit("5/minute")
async def home(request: Request):
    return {"message": "Invoice Reminder API"}


@app.get("/sentry-debug")
async def trigger_error():
    division_by_zero = 1 / 0

from app.api.v1.routes import auth, user, business, invoice, integrations
app.include_router(auth.router)
app.include_router(user.router)
app.include_router(business.router)
app.include_router(invoice.router)
app.include_router(integrations.router)

add_pagination(app)
