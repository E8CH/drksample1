from pydantic import BaseModel


class SalesRow(BaseModel):
    branch_name: str
    address: str
    sale_month: str
    monthly_revenue: float
    electricity_fee: float
    operating_cost: float
    net_profit: float
    occupancy_rate: float


class SalesListResponse(BaseModel):
    data: list[SalesRow]
    total: int
    page: int
    limit: int
