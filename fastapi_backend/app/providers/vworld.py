import logging

import httpx

from app.config import settings
from app.providers.base import MapProvider
from app.schemas.map import BranchPin, Coordinates

logger = logging.getLogger(__name__)

VWORLD_ADDR_URL = "https://api.vworld.kr/req/address"


class VWorldMapProvider(MapProvider):
    async def geocode(self, address: str) -> Coordinates:
        async with httpx.AsyncClient(timeout=10.0) as client:
            for addr_type in ("road", "parcel"):
                try:
                    resp = await client.get(
                        VWORLD_ADDR_URL,
                        params={
                            "service": "address",
                            "request": "getcoord",
                            "version": "2.0",
                            "crs": "epsg:4326",
                            "address": address,
                            "refine": "true",
                            "simple": "false",
                            "format": "json",
                            "type": addr_type,
                            "key": settings.VWORLD_API_KEY,
                        },
                    )
                    resp.raise_for_status()
                    data = resp.json()
                    if data.get("response", {}).get("status") == "OK":
                        point = data["response"]["result"]["point"]
                        lon = float(point.get("x") or 0)
                        lat = float(point.get("y") or 0)
                        if lat and lon:
                            logger.info(
                                "VWORLD geocode OK (%s): %s → lat=%s lon=%s",
                                addr_type, address, lat, lon,
                            )
                            return Coordinates(latitude=lat, longitude=lon)
                except Exception as e:
                    logger.debug("VWORLD geocode (%s) failed: %s", addr_type, e)
                    continue

        raise ValueError(f"VWORLD geocoding 실패: {address}")

    async def get_nearby_branches(
        self, coords: Coordinates, radius_km: float
    ) -> list[BranchPin]:
        return []
