import json
from typing import Optional, Any
from sqlalchemy.orm import Session
from app.models.audit import AuditLog
def log_action(
    db: Session,
    action: str,
    module: str,
    user_id: Optional[int] = None,
    user_name: str = "System",
    user_role: str = "System",
    ip_address: str = "127.0.0.1",
    old_value: Optional[Any] = None,
    new_value: Optional[Any] = None
) -> AuditLog:
    old_str = json.dumps(old_value, default=str) if old_value is not None else None
    new_str = json.dumps(new_value, default=str) if new_value is not None else None
    
    audit_entry = AuditLog(
        user_id=user_id,
        user_name=user_name,
        user_role=user_role,
        action=action,
        module=module,
        ip_address=ip_address,
        old_value=old_str,
        new_value=new_str
    )
    db.add(audit_entry)
    db.commit()
    db.refresh(audit_entry)
    return audit_entry
