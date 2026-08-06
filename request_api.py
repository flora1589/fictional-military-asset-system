from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.request import AssetRequest
from app.models.asset import Asset
from app.models.mission import Mission
from app.models.user import User
from app.schemas.request import (
    AssetRequestOut,
    AssetRequestCreate,
    RequestCommanderAction,
    RequestLogisticsAction,
    RequestTechnicianAction
)
from app.api.deps import require_roles, get_current_user
from app.services.recommendation_engine import recommend_assets_for_mission
from app.services.request_workflow_service import (
    process_commander_review,
    process_logistics_dispatch,
    process_technician_inspection,
    process_mission_completion_and_return
)
from app.services.audit_service import log_action

router = APIRouter(prefix="/requests", tags=["Asset Request Workflow"])

@router.get("", response_model=List[AssetRequestOut])
def list_requests(
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(AssetRequest)
    if status:
        query = query.filter(AssetRequest.status == status)
    if priority:
        query = query.filter(AssetRequest.priority == priority)
        
    # If Unit Officer, default to requests made by their unit/self unless specified
    if current_user.role == "Unit Officer":
        query = query.filter(AssetRequest.requested_by_id == current_user.id)
        
    return query.order_by(AssetRequest.requested_at.desc()).all()

@router.get("/recommendations/{mission_id}")
def get_recommendations(
    mission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return recommend_assets_for_mission(db, mission_id)

@router.post("", response_model=AssetRequestOut, status_code=status.HTTP_201_CREATED)
def create_request(
    req_in: AssetRequestCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["Admin", "Unit Officer", "Commander"]))
):
    mission = db.query(Mission).filter(Mission.id == req_in.mission_id).first()
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")
        
    asset = db.query(Asset).filter(Asset.id == req_in.asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
        
    if asset.maintenance_status in ["Under Maintenance", "Out of Service"]:
        raise HTTPException(
            status_code=400,
            detail=f"Asset '{asset.name}' is currently {asset.maintenance_status} and cannot be requested!"
        )
        
    req_count = db.query(AssetRequest).count()
    req_code = f"REQ-3{1000 + req_count + 1}"
    
    asset_req = AssetRequest(
        request_id=req_code,
        mission_id=req_in.mission_id,
        asset_id=req_in.asset_id,
        requested_by_id=current_user.id,
        priority=req_in.priority,
        reason=req_in.reason,
        status="Submitted"
    )
    db.add(asset_req)
    db.commit()
    db.refresh(asset_req)
    
    log_action(
        db=db,
        action="REQUEST_SUBMITTED",
        module="REQUESTS",
        user_id=current_user.id,
        user_name=current_user.full_name,
        user_role=current_user.role,
        ip_address=request.client.host if request.client else "127.0.0.1",
        new_value={"request_id": asset_req.request_id, "mission_id": req_in.mission_id, "asset_id": req_in.asset_id}
    )
    
    return asset_req

@router.post("/{request_id}/commander-action", response_model=AssetRequestOut)
def commander_action(
    request_id: int,
    action_in: RequestCommanderAction,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["Admin", "Commander"]))
):
    try:
        req, msg = process_commander_review(
            db=db,
            request_id=request_id,
            action=action_in.action,
            notes=action_in.commander_notes or "",
            commander=current_user,
            ip_address=request.client.host if request.client else "127.0.0.1"
        )
        return req
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{request_id}/dispatch", response_model=AssetRequestOut)
def logistics_dispatch(
    request_id: int,
    action_in: RequestLogisticsAction,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["Admin", "Logistics Officer"]))
):
    try:
        req, msg = process_logistics_dispatch(
            db=db,
            request_id=request_id,
            notes=action_in.logistics_notes or "Dispatched from Logistics Depot",
            logistics_officer=current_user,
            ip_address=request.client.host if request.client else "127.0.0.1"
        )
        return req
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{request_id}/inspect", response_model=AssetRequestOut)
def technician_inspect(
    request_id: int,
    action_in: RequestTechnicianAction,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["Admin", "Technician"]))
):
    try:
        req, msg = process_technician_inspection(
            db=db,
            request_id=request_id,
            notes=action_in.technician_notes or "Inspection verified clean",
            condition_rating=action_in.condition_rating,
            fuel_level=action_in.fuel_level,
            battery_status=action_in.battery_status,
            technician=current_user,
            ip_address=request.client.host if request.client else "127.0.0.1"
        )
        return req
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{request_id}/return", response_model=AssetRequestOut)
def return_asset(
    request_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["Admin", "Unit Officer", "Logistics Officer"]))
):
    try:
        req, msg = process_mission_completion_and_return(
            db=db,
            request_id=request_id,
            unit_officer=current_user,
            ip_address=request.client.host if request.client else "127.0.0.1"
        )
        return req
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
