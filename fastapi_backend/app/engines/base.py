from abc import ABC, abstractmethod

from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.simulation import LocationConditions, SimulationResult


class SimulationEngine(ABC):
    @abstractmethod
    async def predict(self, location: LocationConditions, db: AsyncSession) -> SimulationResult: ...
