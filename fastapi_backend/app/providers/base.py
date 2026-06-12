from abc import ABC, abstractmethod

from app.schemas.map import BranchPin, Coordinates


class MapProvider(ABC):
    @abstractmethod
    async def geocode(self, address: str) -> Coordinates: ...

    @abstractmethod
    async def get_nearby_branches(
        self, coords: Coordinates, radius_km: float
    ) -> list[BranchPin]: ...
