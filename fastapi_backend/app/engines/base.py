from abc import ABC, abstractmethod

from app.schemas.simulation import LocationConditions, SimulationResult


class SimulationEngine(ABC):
    @abstractmethod
    async def predict(self, location: LocationConditions) -> SimulationResult: ...
