from app.middleware.logging_middleware import logging_middleware
from fastapi import FastAPI
from app.api.v1.routes import auth, user, business, invoice, integrations
from starlette.middleware.sessions import SessionMiddleware
from fastapi_pagination import add_pagination
from app.core.logging import setup_logger
import sentry_sdk
from sentry_sdk.integrations.asgi import SentryAsgiMiddleware
from app.core.config import settings

logger = setup_logger()

sentry_sdk.init(
    dsn=settings.sentry_dsn,
    # Add data like request headers and IP for users,
    # see https://docs.sentry.io/platforms/python/data-management/data-collected/ for more info
    send_default_pii=True,
)

app = FastAPI()
app.middleware("http")(logging_middleware)
app.add_middleware(SessionMiddleware, secret_key="seom-key")
app.add_middleware(SentryAsgiMiddleware)


@app.get("/")
async def home():
    return {"message": "Invoice Reminder API"}

@app.get("/sentry-debug")
async def trigger_error():
    division_by_zero = 1 / 0


app.include_router(auth.router)
app.include_router(user.router)
app.include_router(business.router)
app.include_router(invoice.router)
app.include_router(integrations.router)

add_pagination(app)
