from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.maintenance import MaintenanceRecord
from app.models.asset import Asset
from app.models.user import User
from app.schemas.maintenance import MaintenanceOut, MaintenanceCreate
from app.api.deps import require_roles, get_current_user
from app.services.audit_service import log_action

router = APIRouter(prefix="/maintenance", tags=["Maintenance & Inspections"])

@router.get("", response_model=List[MaintenanceOut])
def list_maintenance_records(
    asset_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(MaintenanceRecord)
    if asset_id:
        query = query.filter(MaintenanceRecord.asset_id == asset_id)
    if status:
        query = query.filter(MaintenanceRecord.status == status)
    return query.order_by(MaintenanceRecord.service_date.desc()).all()

@router.post("", response_model=MaintenanceOut, status_code=status.HTTP_201_CREATED)
def create_maintenance_record(
    record_in: MaintenanceCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["Admin", "Technician"]))
):
    asset = db.query(Asset).filter(Asset.id == record_in.asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
        
    mnt_count = db.query(MaintenanceRecord).count()
    rec_code = f"MNT-4{1000 + mnt_count + 1}"
    
    record = MaintenanceRecord(
        record_id=rec_code,
        asset_id=record_in.asset_id,
        technician_id=current_user.id,
        service_type=record_in.service_type,
        description=record_in.description,
        mileage=record_in.mileage,
        fuel_level=record_in.fuel_level,
        battery_status=record_in.battery_status,
        condition_before=record_in.condition_before,
        condition_after=record_in.condition_after,
        status=record_in.status
    )
    db.add(record)
    
    # Update asset specs & maintenance status
    asset.condition = record_in.condition_after
    asset.fuel_level = record_in.fuel_level
    asset.battery_status = record_in.battery_status
    asset.mileage = record_in.mileage
    asset.last_service_date = datetime.now(timezone.utc)
    
    if record_in.status in ["In Progress", "Under Maintenance"]:
        asset.maintenance_status = "Under Maintenance"
        asset.availability = "Under Maintenance"
    elif record_in.status == "Completed":
        asset.maintenance_status = "Healthy"
        asset.availability = "Available"
    elif record_in.status == "Out of Service":
        asset.maintenance_status = "Out of Service"
        asset.availability = "Out of Service"
        
    db.commit()
    db.refresh(record)
    
    log_action(
        db=db,
        action="MAINTENANCE_RECORDED",
        module="MAINTENANCE",
        user_id=current_user.id,
        user_name=current_user.full_name,
        user_role=current_user.role,
        ip_address=request.client.host if request.client else "127.0.0.1",
        new_value={"asset_id": asset.asset_id, "service_type": record.service_type, "status": record.status}
    )
    
    return record
