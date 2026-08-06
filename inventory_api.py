from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.inventory import InventoryItem
from app.models.notification import Notification
from app.models.user import User
from app.schemas.inventory import InventoryOut, InventoryCreate, InventoryUpdate
from app.api.deps import require_roles, get_current_user
from app.services.audit_service import log_action

router = APIRouter(prefix="/inventory", tags=["Inventory Management"])

@router.get("", response_model=List[InventoryOut])
def list_inventory(
    category: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(InventoryItem)
    if category:
        query = query.filter(InventoryItem.category == category)
    if status:
        query = query.filter(InventoryItem.status == status)
    return query.all()

@router.post("", response_model=InventoryOut, status_code=status.HTTP_201_CREATED)
def create_inventory_item(
    item_in: InventoryCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["Admin", "Logistics Officer"]))
):
    existing = db.query(InventoryItem).filter(InventoryItem.item_code == item_in.item_code).first()
    if existing:
        raise HTTPException(status_code=400, detail="Item code already exists")
        
    status_str = "Sufficient"
    if item_in.quantity <= 0:
        status_str = "Out of Stock"
    elif item_in.quantity <= item_in.reorder_level * 0.5:
        status_str = "Critical Stock"
    elif item_in.quantity <= item_in.reorder_level:
        status_str = "Low Stock"
        
    item = InventoryItem(
        **item_in.model_dump(),
        status=status_str
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    
    log_action(
        db=db,
        action="INVENTORY_ITEM_CREATED",
        module="INVENTORY",
        user_id=current_user.id,
        user_name=current_user.full_name,
        user_role=current_user.role,
        ip_address=request.client.host if request.client else "127.0.0.1",
        new_value={"item_code": item.item_code, "name": item.name, "quantity": item.quantity}
    )
    return item

@router.put("/{item_id}", response_model=InventoryOut)
def update_inventory_item(
    item_id: int,
    item_in: InventoryUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["Admin", "Logistics Officer"]))
):
    item = db.query(InventoryItem).filter(InventoryItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Inventory item not found")
        
    old_qty = item.quantity
    update_data = item_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(item, field, value)
        
    # Re-evaluate stock status
    if item.quantity <= 0:
        item.status = "Out of Stock"
    elif item.quantity <= item.reorder_level * 0.5:
        item.status = "Critical Stock"
    elif item.quantity <= item.reorder_level:
        item.status = "Low Stock"
    else:
        item.status = "Sufficient"
        
    # Trigger low inventory alert notification if low or critical
    if item.status in ["Low Stock", "Critical Stock", "Out of Stock"]:
        notif = Notification(
            target_role="Logistics Officer",
            title=f"Low Stock Alert: {item.name}",
            message=f"Item {item.name} ({item.item_code}) quantity dropped to {item.quantity} {item.unit}. (Reorder threshold: {item.reorder_level})",
            type="WARNING" if item.status == "Low Stock" else "DANGER"
        )
        db.add(notif)
        
    db.commit()
    db.refresh(item)
    
    log_action(
        db=db,
        action="INVENTORY_UPDATED",
        module="INVENTORY",
        user_id=current_user.id,
        user_name=current_user.full_name,
        user_role=current_user.role,
        ip_address=request.client.host if request.client else "127.0.0.1",
        old_value={"quantity": old_qty},
        new_value={"quantity": item.quantity, "status": item.status}
    )
    return item
