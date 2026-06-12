from sqlalchemy.ext.asyncio import AsyncSession

from app.engines.base import SimulationEngine
from app.engines.rule_based import RuleBasedEngine
from app.schemas.simulation import LocationConditions, SimulationResult


class MLEngine(SimulationEngine):
    async def predict(self, location: LocationConditions, db: AsyncSession) -> SimulationResult:
        # TODO: scripts/train_model.py ML 모델 추론으로 교체 (v2)
        return await RuleBasedEngine().predict(location, db)
