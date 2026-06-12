from typing import Optional

from pydantic import BaseModel


class LocationConditions(BaseModel):
    address: str
    area_sqm: float
    monthly_rent: float
    monthly_maintenance: Optional[float] = None
    building_usage: Optional[str] = None
    ev_charging: bool = False
    parking_count: int = 0


class SimulationResult(BaseModel):
    estimated_monthly_revenue: float
    occupancy_rate: float
    net_profit: float
    percentile: float
    verdict: str  # "추천" | "검토필요" | "비추천"
    similar_branch_count: int
    fallback_used: bool = False
