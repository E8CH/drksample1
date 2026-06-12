from typing import Literal, Optional

from pydantic import BaseModel, Field


class LocationConditions(BaseModel):
    address: str = Field(min_length=1)
    area_sqm: float = Field(gt=0)
    monthly_rent: float = Field(gt=0)
    monthly_maintenance: Optional[float] = Field(default=None, ge=0)
    building_usage: Optional[str] = None
    ev_charging: bool = False
    parking_count: int = Field(default=0, ge=0)


class SimulationResult(BaseModel):
    estimated_monthly_revenue: float
    occupancy_rate: float
    net_profit: float
    percentile: float
    verdict: Literal["추천", "검토필요", "비추천"]
    similar_branch_count: int
    fallback_used: bool = False
