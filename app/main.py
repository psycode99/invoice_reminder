from app.middleware.logging_middleware import logging_middleware
from fastapi import FastAPI
from app.api.v1.routes import auth, user, business, invoice, integrations
from starlette.middleware.sessions import SessionMiddleware
from fastapi_pagination import add_pagination
from app.core.logging import setup_logger


logger = setup_logger()

app = FastAPI()
app.middleware("http")(logging_middleware)
app.add_middleware(SessionMiddleware, secret_key="seom-key")


@app.get("/")
async def home():
    return {"message": "Invoice Reminder API"}


app.include_router(auth.router)
app.include_router(user.router)
app.include_router(business.router)
app.include_router(invoice.router)
app.include_router(integrations.router)

add_pagination(app)
