from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base
class Role(Base):
    __tablename__ = "roles"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, index=True, nullable=False) # Admin, Commander, Logistics Officer, Technician, Unit Officer
    description = Column(String(255), nullable=True)
    permissions = Column(Text, nullable=True) # JSON or comma separated permissions list
    users = relationship("User", back_populates="role_obj")
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(100), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=False)
    role = Column(String(50), nullable=False) # Admin, Commander, Logistics Officer, Technician, Unit Officer
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=True)
    unit = Column(String(100), nullable=True)
    rank = Column(String(50), nullable=True)
    service_id = Column(String(50), unique=True, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    role_obj = relationship("Role", back_populates="users")
    missions_created = relationship("Mission", back_populates="created_by")
    requests_made = relationship("AssetRequest", back_populates="requested_by")
