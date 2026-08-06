from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.audit import AuditLog
from app.models.user import User
from app.schemas.notification import AuditLogOut
from app.api.deps import require_roles, get_current_user

router = APIRouter(prefix="/audit-logs", tags=["Audit Trail"])

@router.get("", response_model=List[AuditLogOut])
def list_audit_logs(
    module: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    user_role: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["Admin"]))
):
    query = db.query(AuditLog)
    if module:
        query = query.filter(AuditLog.module == module)
    if action:
        query = query.filter(AuditLog.action.ilike(f"%{action}%"))
    if user_role:
        query = query.filter(AuditLog.user_role == user_role)
        
    return query.order_by(AuditLog.timestamp.desc()).limit(limit).all()
