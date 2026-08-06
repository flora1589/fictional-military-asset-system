from datetime import datetime
from typing import Optional
from pydantic import BaseModel
class NotificationOut(BaseModel):
    id: int
    user_id: Optional[int] = None
    target_role: Optional[str] = None
    title: str
    message: str
    type: str
    is_read: bool
    created_at: datetime
    class Config:
        from_attributes = True
class AuditLogOut(BaseModel):
    id: int
    user_id: Optional[int] = None
    user_name: str
    user_role: str
    action: str
    module: str
    ip_address: str
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    timestamp: datetime
    class Config:
        from_attributes = True
class ReportOut(BaseModel):
    id: int
    report_name: str
    report_type: str
    generated_by: str
    file_format: str
    file_path: Optional[str] = None
    generated_at: datetime
    class Config:
        from_attributes = True
