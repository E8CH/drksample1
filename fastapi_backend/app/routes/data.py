from fastapi import APIRouter, BackgroundTasks, Cookie, Depends, HTTPException
import jwt

from app.config import settings
from app.services.data_generator import _STATUS, generate_all_data, delete_all_data

router = APIRouter(prefix="/data", tags=["data"])


async def require_admin(access_token: str | None = Cookie(None)) -> str:
    if not access_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = jwt.decode(
            access_token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
            options={"require": ["exp", "sub"]},
        )
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    if str(payload["sub"]) != settings.ADMIN_USERNAME:
        raise HTTPException(status_code=403, detail="Admin access required")
    return str(payload["sub"])


@router.post("/generate", status_code=202)
async def generate_data(
    background_tasks: BackgroundTasks,
    _: str = Depends(require_admin),
):
    if _STATUS["value"] == "running":
        raise HTTPException(status_code=409, detail="Generation already in progress")
    _STATUS["value"] = "running"
    background_tasks.add_task(generate_all_data)
    return {"status": "generating"}


@router.get("/status")
async def get_status(_: str = Depends(require_admin)):
    return {"status": _STATUS["value"]}


@router.delete("/all")
async def delete_all(_: str = Depends(require_admin)):
    if _STATUS["value"] == "running":
        raise HTTPException(status_code=409, detail="Generation in progress")
    await delete_all_data()
    return {"deleted": True}
