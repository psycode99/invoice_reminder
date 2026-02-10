from fastapi import FastAPI
from app.api.v1.routes import auth, user, business, invoice
from starlette.middleware.sessions import SessionMiddleware
from fastapi_pagination import add_pagination
from app.core.logging import LOGGING_CONFIG
from logging.config import dictConfig

dictConfig(LOGGING_CONFIG)

app = FastAPI()


app.add_middleware(SessionMiddleware, secret_key="seom-key")


@app.get("/")
async def home():
    return {"message": "Invoice Reminder API"}


app.include_router(auth.router)
app.include_router(user.router)
app.include_router(business.router)
app.include_router(invoice.router)

add_pagination(app)
