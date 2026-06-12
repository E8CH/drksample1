import jwt
from fastapi import APIRouter, Cookie, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_async_session
from app.schemas.simulation import LocationConditions, SimulationResult
from app.services.simulation_service import get_engine

router = APIRouter(prefix="/simulation", tags=["simulation"])


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


@router.post("/run", response_model=SimulationResult)
async def run_simulation(
    location: LocationConditions,
    _: str = Depends(require_admin),
    db: AsyncSession = Depends(get_async_session),
) -> SimulationResult:
    engine = get_engine()
    return await engine.predict(location, db)
