from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel
from app.schemas.user import UserOut
from app.schemas.asset import AssetOut
from app.schemas.mission import MissionOut
class AssetRequestCreate(BaseModel):
    mission_id: int
    asset_id: int
    priority: str = "Medium"
    reason: Optional[str] = None
class RequestCommanderAction(BaseModel):
    action: str # Approve or Reject
    commander_notes: Optional[str] = None
class RequestLogisticsAction(BaseModel):
    logistics_notes: Optional[str] = None
    dispatch_location: Optional[str] = None
class RequestTechnicianAction(BaseModel):
    technician_notes: Optional[str] = None
    condition_rating: str = "Good"
    fuel_level: float = 100.0
    battery_status: float = 100.0
class AssetRequestOut(BaseModel):
    id: int
    request_id: str
    mission_id: int
    asset_id: int
    requested_by_id: int
    status: str
    priority: str
    reason: Optional[str] = None
    commander_notes: Optional[str] = None
    commander_action_at: Optional[datetime] = None
    logistics_notes: Optional[str] = None
    dispatched_at: Optional[datetime] = None
    technician_notes: Optional[str] = None
    inspected_at: Optional[datetime] = None
    returned_at: Optional[datetime] = None
    requested_at: datetime
    updated_at: datetime
    
    mission: Optional[MissionOut] = None
    asset: Optional[AssetOut] = None
    requested_by: Optional[UserOut] = None
    class Config:
        from_attributes = True
