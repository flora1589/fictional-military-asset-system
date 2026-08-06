from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.mission import Mission
from app.models.user import User
from app.schemas.mission import MissionOut, MissionCreate, MissionUpdate
from app.api.deps import require_roles, get_current_user
from app.services.audit_service import log_action

router = APIRouter(prefix="/missions", tags=["Mission Planning"])

@router.get("", response_model=List[MissionOut])
def list_missions(
    status: Optional[str] = Query(None),
    mission_type: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Mission)
    if status:
        query = query.filter(Mission.status == status)
    if mission_type:
        query = query.filter(Mission.mission_type == mission_type)
    if priority:
        query = query.filter(Mission.priority == priority)
    return query.order_by(Mission.created_at.desc()).all()

@router.get("/{mission_id}", response_model=MissionOut)
def get_mission(
    mission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    mission = db.query(Mission).filter(Mission.id == mission_id).first()
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")
    return mission

@router.post("", response_model=MissionOut, status_code=status.HTTP_201_CREATED)
def create_mission(
    mission_in: MissionCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["Admin", "Commander", "Unit Officer"]))
):
    existing = db.query(Mission).filter(Mission.mission_id == mission_in.mission_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Mission ID already exists")
        
    mission = Mission(
        **mission_in.model_dump(),
        created_by_id=current_user.id
    )
    db.add(mission)
    db.commit()
    db.refresh(mission)
    
    log_action(
        db=db,
        action="MISSION_CREATED",
        module="MISSIONS",
        user_id=current_user.id,
        user_name=current_user.full_name,
        user_role=current_user.role,
        ip_address=request.client.host if request.client else "127.0.0.1",
        new_value={"mission_id": mission.mission_id, "name": mission.name, "type": mission.mission_type}
    )
    
    return mission

@router.put("/{mission_id}", response_model=MissionOut)
def update_mission(
    mission_id: int,
    mission_in: MissionUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["Admin", "Commander", "Unit Officer"]))
):
    mission = db.query(Mission).filter(Mission.id == mission_id).first()
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")
        
    old_status = mission.status
    update_data = mission_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(mission, field, value)
        
    db.commit()
    db.refresh(mission)
    
    log_action(
        db=db,
        action="MISSION_UPDATED",
        module="MISSIONS",
        user_id=current_user.id,
        user_name=current_user.full_name,
        user_role=current_user.role,
        ip_address=request.client.host if request.client else "127.0.0.1",
        old_value={"status": old_status},
        new_value={"status": mission.status}
    )
    
    return mission
