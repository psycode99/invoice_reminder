from fastapi import Request
from app.core.security import decode_jwt


async def attach_user(request: Request, call_next):
    auth = request.headers.get("Authorization")

    if auth and auth.startswith("Bearer "):
        token = auth.split(" ")[1]
        decode_token = decode_jwt(token)
        request.state.user_id = decode_token.get("sub")

    response = await call_next(request)
    return response
