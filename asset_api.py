from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc, asc
from app.core.database import get_db
from app.models.asset import Asset
from app.models.user import User
from app.schemas.asset import AssetOut, AssetCreate, AssetUpdate, AssetPaginated
from app.api.deps import require_roles, get_current_user
from app.services.audit_service import log_action

router = APIRouter(prefix="/assets", tags=["Asset Management"])

@router.get("", response_model=AssetPaginated)
def list_assets(
    search: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    availability: Optional[str] = Query(None),
    maintenance_status: Optional[str] = Query(None),
    assigned_unit: Optional[str] = Query(None),
    sort_by: Optional[str] = Query("id"),
    order: Optional[str] = Query("asc"),
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Asset)
    
    if search:
        pattern = f"%{search}%"
        query = query.filter(
            or_(
                Asset.name.ilike(pattern),
                Asset.asset_id.ilike(pattern),
                Asset.type.ilike(pattern),
                Asset.serial_number.ilike(pattern),
                Asset.manufacturer.ilike(pattern),
                Asset.current_location.ilike(pattern)
            )
        )
        
    if category:
        query = query.filter(Asset.category == category)
    if availability:
        query = query.filter(Asset.availability == availability)
    if maintenance_status:
        query = query.filter(Asset.maintenance_status == maintenance_status)
    if assigned_unit:
        query = query.filter(Asset.assigned_unit == assigned_unit)
        
    # Dynamic sorting
    sort_attr = getattr(Asset, sort_by, Asset.id)
    if order.lower() == "desc":
        query = query.order_by(desc(sort_attr))
    else:
        query = query.order_by(asc(sort_attr))
        
    total = query.count()
    items = query.offset((page - 1) * size).limit(size).all()
    
    return AssetPaginated(
        total=total,
        page=page,
        size=size,
        items=[AssetOut.model_validate(item) for item in items]
    )

@router.get("/{asset_id}", response_model=AssetOut)
def get_asset(
    asset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return asset

@router.post("", response_model=AssetOut, status_code=status.HTTP_201_CREATED)
def create_asset(
    asset_in: AssetCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["Admin", "Logistics Officer"]))
):
    existing = db.query(Asset).filter(
        or_(Asset.asset_id == asset_in.asset_id, Asset.serial_number == asset_in.serial_number)
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Asset with this Asset ID or Serial Number already exists")
        
    asset = Asset(**asset_in.model_dump())
    db.add(asset)
    db.commit()
    db.refresh(asset)
    
    log_action(
        db=db,
        action="ASSET_CREATED",
        module="ASSETS",
        user_id=current_user.id,
        user_name=current_user.full_name,
        user_role=current_user.role,
        ip_address=request.client.host if request.client else "127.0.0.1",
        new_value={"asset_id": asset.asset_id, "name": asset.name, "category": asset.category}
    )
    
    return asset

@router.put("/{asset_id}", response_model=AssetOut)
def update_asset(
    asset_id: int,
    asset_in: AssetUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["Admin", "Logistics Officer", "Technician"]))
):
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
        
    old_val = {
        "name": asset.name,
        "fuel_level": asset.fuel_level,
        "condition": asset.condition,
        "maintenance_status": asset.maintenance_status,
        "availability": asset.availability
    }
    
    update_data = asset_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(asset, field, value)
        
    db.commit()
    db.refresh(asset)
    
    log_action(
        db=db,
        action="ASSET_UPDATED",
        module="ASSETS",
        user_id=current_user.id,
        user_name=current_user.full_name,
        user_role=current_user.role,
        ip_address=request.client.host if request.client else "127.0.0.1",
        old_value=old_val,
        new_value={"name": asset.name, "condition": asset.condition, "maintenance_status": asset.maintenance_status}
    )
    
    return asset

@router.delete("/{asset_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_asset(
    asset_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["Admin"]))
):
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
        
    db.delete(asset)
    db.commit()
    
    log_action(
        db=db,
        action="ASSET_DELETED",
        module="ASSETS",
        user_id=current_user.id,
        user_name=current_user.full_name,
        user_role=current_user.role,
        ip_address=request.client.host if request.client else "127.0.0.1",
        old_value={"id": asset_id, "asset_id": asset.asset_id}
    )
    return None
