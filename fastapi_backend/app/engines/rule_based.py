from app.engines.base import SimulationEngine
from app.schemas.simulation import LocationConditions, SimulationResult


class RuleBasedEngine(SimulationEngine):
    async def predict(self, location: LocationConditions) -> SimulationResult:
        # Story 2.2에서 완전 구현 (FR-2: 유사 지점 추출 → 가중 평균 → EV/주차 보정 → 판정)
        return SimulationResult(
            estimated_monthly_revenue=0.0,
            occupancy_rate=0.0,
            net_profit=0.0,
            percentile=0.0,
            verdict="검토필요",
            similar_branch_count=0,
        )
