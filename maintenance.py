from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from app.schemas.asset import AssetOut
from app.schemas.user import UserOut
class MaintenanceCreate(BaseModel):
    asset_id: int
    service_type: str
    description: str
    mileage: float = 0.0
    fuel_level: float = 100.0
    battery_status: float = 100.0
    condition_before: str
    condition_after: str
    status: str = "Completed"
class MaintenanceOut(BaseModel):
    id: int
    record_id: str
    asset_id: int
    technician_id: int
    service_type: str
    description: str
    mileage: float
    fuel_level: float
    battery_status: float
    condition_before: str
    condition_after: str
    status: str
    service_date: datetime
    
    asset: Optional[AssetOut] = None
    technician: Optional[UserOut] = None
    class Config:
        from_attributes = True
