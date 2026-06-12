from pydantic import BaseModel


class Coordinates(BaseModel):
    latitude: float
    longitude: float


class BranchPin(BaseModel):
    branch_name: str
    address: str
    latitude: float
    longitude: float
