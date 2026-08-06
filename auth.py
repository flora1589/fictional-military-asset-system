from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import verify_password, create_access_token, get_password_hash
from app.models.user import User
from app.schemas.user import Token, UserOut, UserCreate, UserUpdate
from app.api.deps import get_current_user
from app.services.audit_service import log_action

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/login", response_model=Token)
def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Account disabled")
        
    access_token = create_access_token(subject=user.id, role=user.role)
    
    # Audit log login
    log_action(
        db=db,
        action="USER_LOGIN",
        module="AUTH",
        user_id=user.id,
        user_name=user.full_name,
        user_role=user.role,
        ip_address=request.client.host if request.client else "127.0.0.1"
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": UserOut.model_validate(user)
    }

@router.get("/me", response_model=UserOut)
def read_current_user(current_user: User = Depends(get_current_user)):
    return current_user

@router.put("/profile", response_model=UserOut)
def update_profile(
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if user_update.full_name:
        current_user.full_name = user_update.full_name
    if user_update.unit:
        current_user.unit = user_update.unit
    if user_update.rank:
        current_user.rank = user_update.rank
    if user_update.password:
        current_user.password_hash = get_password_hash(user_update.password)
        
    db.commit()
    db.refresh(current_user)
    return current_user
