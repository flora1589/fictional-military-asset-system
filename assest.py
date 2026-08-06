from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean
from sqlalchemy.orm import relationship
from app.core.database import Base
class Asset(Base):
    __tablename__ = "assets"
    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(String(50), unique=True, index=True, nullable=False) # e.g. AST-1001
    name = Column(String(100), nullable=False)
    category = Column(String(50), nullable=False) # Vehicle, Aircraft, Maritime, Communications, Medical, Supply
    type = Column(String(50), nullable=False) # Armored Vehicle, Ambulance, Helicopter, Rescue Boat, Transport Truck
    serial_number = Column(String(100), unique=True, nullable=False)
    manufacturer = Column(String(100), nullable=False)
    purchase_date = Column(DateTime, nullable=True)
    fuel_level = Column(Float, default=100.0) # Percentage 0-100
    battery_status = Column(Float, default=100.0) # Percentage 0-100
    mileage = Column(Float, default=0.0) # Kilometers / Hours
    condition = Column(String(50), default="Excellent") # Excellent, Good, Fair, Poor, Critical
    maintenance_status = Column(String(50), default="Healthy") # Healthy, Needs Service, Under Maintenance, Out of Service
    availability = Column(String(50), default="Available") # Available, Assigned, In Mission, Under Maintenance
    assigned_unit = Column(String(100), default="Unassigned")
    current_location = Column(String(100), default="Base Depot Alpha")
    last_service_date = Column(DateTime, nullable=True)
    next_service_date = Column(DateTime, nullable=True)
    image_url = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    requests = relationship("AssetRequest", back_populates="asset")
    maintenance_records = relationship("MaintenanceRecord", back_populates="asset")
