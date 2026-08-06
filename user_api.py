from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_password_hash
from app.models.user import User, Role
from app.schemas.user import UserOut, UserCreate, UserUpdate, RoleOut, RoleCreate
from app.api.deps import require_roles, get_current_user
from app.services.audit_service import log_action

router = APIRouter(prefix="/users", tags=["Users & Roles"])

@router.get("", response_model=List[UserOut])
def list_users(
    role: Optional[str] = Query(None),
    unit: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["Admin", "Commander", "Logistics Officer"]))
):
    query = db.query(User)
    if role:
        query = query.filter(User.role == role)
    if unit:
        query = query.filter(User.unit == unit)
    return query.all()

@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(
    user_in: UserCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["Admin"]))
):
    existing = db.query(User).filter(User.email == user_in.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="User with this email already exists")
        
    hashed_pwd = get_password_hash(user_in.password)
    user = User(
        email=user_in.email,
        password_hash=hashed_pwd,
        full_name=user_in.full_name,
        role=user_in.role,
        unit=user_in.unit,
        rank=user_in.rank,
        service_id=user_in.service_id
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    log_action(
        db=db,
        action="USER_CREATED",
        module="USERS",
        user_id=current_user.id,
        user_name=current_user.full_name,
        user_role=current_user.role,
        ip_address=request.client.host if request.client else "127.0.0.1",
        new_value={"email": user.email, "role": user.role}
    )
    
    return user

@router.get("/roles", response_model=List[RoleOut])
def list_roles(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(Role).all()

@router.put("/{user_id}", response_model=UserOut)
def update_user(
    user_id: int,
    user_in: UserUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["Admin"]))
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    old_val = {"full_name": user.full_name, "role": user.role, "is_active": user.is_active}
    
    if user_in.full_name is not None:
        user.full_name = user_in.full_name
    if user_in.role is not None:
        user.role = user_in.role
    if user_in.unit is not None:
        user.unit = user_in.unit
    if user_in.rank is not None:
        user.rank = user_in.rank
    if user_in.is_active is not None:
        user.is_active = user_in.is_active
    if user_in.password:
        user.password_hash = get_password_hash(user_in.password)
        
    db.commit()
    db.refresh(user)
    
    log_action(
        db=db,
        action="USER_UPDATED",
        module="USERS",
        user_id=current_user.id,
        user_name=current_user.full_name,
        user_role=current_user.role,
        ip_address=request.client.host if request.client else "127.0.0.1",
        old_value=old_val,
        new_value={"full_name": user.full_name, "role": user.role, "is_active": user.is_active}
    )
    
    return user

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["Admin"]))
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    db.delete(user)
    db.commit()
    
    log_action(
        db=db,
        action="USER_DELETED",
        module="USERS",
        user_id=current_user.id,
        user_name=current_user.full_name,
        user_role=current_user.role,
        ip_address=request.client.host if request.client else "127.0.0.1",
        old_value={"id": user_id, "email": user.email}
    )
    return None
