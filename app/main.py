from fastapi import FastAPI
from app.api.v1.routes import auth
from starlette.middleware.sessions import SessionMiddleware

app = FastAPI()

app.add_middleware(
    SessionMiddleware, secret_key="seom-key"
)

@app.get('/')
async def home():
    return {"message": "Invoice Reminder API"}

app.include_router(auth.router)