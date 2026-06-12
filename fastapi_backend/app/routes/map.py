import logging
import math

import httpx
import jwt
from fastapi import APIRouter, Cookie, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_async_session
from app.models.branch import Branch
from app.schemas.map import BranchPin, Coordinates
from app.services import map_service

router = APIRouter(prefix="/branches", tags=["map"])
logger = logging.getLogger(__name__)


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
        return str(payload["sub"])
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    return R * 2 * math.asin(math.sqrt(max(0.0, min(1.0, a))))


@router.get("/nearby")
async def get_nearby_branches(
    address: str,
    radius_km: float = Query(default=2.0, gt=0.0, le=50.0),
    _: str = Depends(require_admin),
    db: AsyncSession = Depends(get_async_session),
) -> dict:
    try:
        target: Coordinates = await map_service.geocode(address)
    except (ValueError, httpx.HTTPError, httpx.TimeoutException) as exc:
        logger.warning("Geocoding failed for address=%r: %s", address, exc)
        raise HTTPException(
            status_code=422,
            detail={"detail": "주소 변환 실패", "address": address},
        )

    # Bounding box pre-filter to avoid full table scan
    lat_delta = radius_km / 111.0
    lon_delta = radius_km / max(111.0 * math.cos(math.radians(target.latitude)), 0.01)

    stmt = select(Branch).where(
        Branch.latitude.isnot(None),
        Branch.longitude.isnot(None),
        Branch.latitude.between(target.latitude - lat_delta, target.latitude + lat_delta),
        Branch.longitude.between(target.longitude - lon_delta, target.longitude + lon_delta),
    )
    rows = (await db.execute(stmt)).scalars().all()

    pins: list[BranchPin] = [
        BranchPin(
            branch_name=b.branch_name,
            address=b.address,
            latitude=float(b.latitude),
            longitude=float(b.longitude),
        )
        for b in rows
        if _haversine_km(
            target.latitude, target.longitude, float(b.latitude), float(b.longitude)
        )
        <= radius_km
    ]

    return {"target": target.model_dump(), "pins": [p.model_dump() for p in pins]}
