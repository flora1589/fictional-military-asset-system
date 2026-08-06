from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel
from app.schemas.user import UserOut
class MissionBase(BaseModel):
    name: str
    mission_type: str # Patrol, Rescue, Medical, Training, Logistics, Border Security
    priority: str = "Medium" # Low, Medium, High, Critical
    description: Optional[str] = None
    start_date: datetime
    end_date: datetime
    destination: str
    personnel_count: int = 1
    status: str = "Planned" # Planned, Active, Completed, Cancelled
class MissionCreate(MissionBase):
    mission_id: str
class MissionUpdate(BaseModel):
    name: Optional[str] = None
    mission_type: Optional[str] = None
    priority: Optional[str] = None
    description: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    destination: Optional[str] = None
    personnel_count: Optional[int] = None
    status: Optional[str] = None
class MissionOut(MissionBase):
    id: int
    mission_id: str
    created_by_id: int
    created_at: datetime
    created_by: Optional[UserOut] = None
    class Config:
        from_attributes = True
