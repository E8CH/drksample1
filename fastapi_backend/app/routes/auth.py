from datetime import datetime, timedelta, timezone

import jwt
from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel

from app.config import settings

router = APIRouter(prefix="/auth", tags=["custom-auth"])


class LoginRequest(BaseModel):
    username: str
    password: str


@router.post("/login")
async def login(request: LoginRequest, response: Response):
    if request.username != settings.ADMIN_USERNAME or request.password != settings.ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="로그인 정보가 올바르지 않습니다")
    expire = datetime.now(timezone.utc) + timedelta(seconds=settings.ACCESS_TOKEN_EXPIRE_SECONDS)
    token = jwt.encode(
        {"sub": request.username, "exp": expire},
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        max_age=settings.ACCESS_TOKEN_EXPIRE_SECONDS,
        samesite="lax",
        secure=False,
    )
    return {"access_token": token, "message": "ok"}


@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie("access_token", httponly=True, samesite="lax")
    return {"message": "ok"}
