from datetime import datetime
from typing import Optional
from pydantic import BaseModel
class InventoryCreate(BaseModel):
    item_code: str
    name: str
    category: str
    quantity: float
    unit: str = "units"
    reorder_level: float = 10.0
    location: str = "Depot Store House 1"
class InventoryUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    quantity: Optional[float] = None
    unit: Optional[str] = None
    reorder_level: Optional[float] = None
    location: Optional[str] = None
class InventoryOut(BaseModel):
    id: int
    item_code: str
    name: str
    category: str
    quantity: float
    unit: str
    reorder_level: float
    location: str
    status: str
    last_updated: datetime
    class Config:
        from_attributes = True
