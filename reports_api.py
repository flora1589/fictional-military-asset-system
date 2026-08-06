from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import get_db
from app.models.asset import Asset
from app.models.mission import Mission
from app.models.request import AssetRequest
from app.models.maintenance import MaintenanceRecord
from app.models.inventory import InventoryItem
from app.models.notification import Notification
from app.models.user import User
from app.models.audit import AuditLog
from app.schemas.notification import ReportOut
from app.api.deps import require_roles, get_current_user
from app.services.report_service import generate_pdf_report, generate_excel_report, generate_csv_report

router = APIRouter(prefix="/reports", tags=["Reports & Analytics"])

@router.get("/dashboard-stats")
def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    total_assets = db.query(Asset).count()
    available_assets = db.query(Asset).filter(Asset.availability == "Available").count()
    assets_in_mission = db.query(Asset).filter(Asset.availability == "In Mission").count()
    assets_maintenance = db.query(Asset).filter(Asset.maintenance_status == "Under Maintenance").count()
    
    pending_requests = db.query(AssetRequest).filter(AssetRequest.status.in_(["Submitted", "Pending Commander Review"])).count()
    active_missions = db.query(Mission).filter(Mission.status == "Active").count()
    
    low_inventory_alerts = db.query(InventoryItem).filter(InventoryItem.status.in_(["Low Stock", "Critical Stock", "Out of Stock"])).count()
    critical_notifications = db.query(Notification).filter(Notification.type == "CRITICAL", Notification.is_read == False).count()
    
    # Chart 1: Asset Utilization
    utilization_chart = [
        {"name": "Available", "value": available_assets},
        {"name": "In Mission", "value": assets_in_mission},
        {"name": "Under Maintenance", "value": assets_maintenance},
        {"name": "Assigned/Dispatched", "value": db.query(Asset).filter(Asset.availability == "Assigned").count()}
    ]
    
    # Chart 2: Mission Categories
    mission_categories = db.query(
        Mission.mission_type, func.count(Mission.id)
    ).group_by(Mission.mission_type).all()
    mission_cat_chart = [{"type": cat, "count": count} for cat, count in mission_categories]
    
    # Chart 3: Approval Statistics
    approved_count = db.query(AssetRequest).filter(AssetRequest.status == "Approved").count()
    rejected_count = db.query(AssetRequest).filter(AssetRequest.status == "Rejected").count()
    dispatched_count = db.query(AssetRequest).filter(AssetRequest.status.in_(["Dispatched", "Inspected & Active", "Returned & Completed"])).count()
    approval_chart = [
        {"status": "Approved", "count": approved_count},
        {"status": "Rejected", "count": rejected_count},
        {"status": "Dispatched", "count": dispatched_count},
        {"status": "Pending", "count": pending_requests}
    ]
    
    # Chart 4: Maintenance Statistics
    healthy_count = db.query(Asset).filter(Asset.maintenance_status == "Healthy").count()
    needs_service_count = db.query(Asset).filter(Asset.maintenance_status == "Needs Service").count()
    under_mnt_count = assets_maintenance
    out_service_count = db.query(Asset).filter(Asset.maintenance_status == "Out of Service").count()
    maintenance_chart = [
        {"status": "Healthy", "count": healthy_count},
        {"status": "Needs Service", "count": needs_service_count},
        {"status": "Under Maintenance", "count": under_mnt_count},
        {"status": "Out of Service", "count": out_service_count}
    ]
    
    return {
        "summary": {
            "total_assets": total_assets,
            "available_assets": available_assets,
            "assets_in_mission": assets_in_mission,
            "assets_under_maintenance": assets_maintenance,
            "pending_requests": pending_requests,
            "active_missions": active_missions,
            "low_inventory_alerts": low_inventory_alerts,
            "critical_notifications": critical_notifications
        },
        "charts": {
            "asset_utilization": utilization_chart,
            "mission_categories": mission_cat_chart,
            "approval_stats": approval_chart,
            "maintenance_stats": maintenance_chart
        }
    }

@router.get("/export")
def export_report(
    report_type: str = Query(..., description="Mission, Asset, Maintenance, Request, Inventory"),
    file_format: str = Query("PDF", description="PDF, XLSX, CSV"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["Admin", "Commander", "Logistics Officer"]))
):
    data: List[Dict[str, Any]] = []
    title = f"{report_type} Summary Report"
    
    if report_type.lower() == "asset":
        assets = db.query(Asset).all()
        data = [{
            "Asset ID": a.asset_id,
            "Name": a.name,
            "Category": a.category,
            "Type": a.type,
            "Condition": a.condition,
            "Status": a.maintenance_status,
            "Availability": a.availability,
            "Fuel (%)": a.fuel_level,
            "Battery (%)": a.battery_status,
            "Location": a.current_location
        } for a in assets]
        
    elif report_type.lower() == "mission":
        missions = db.query(Mission).all()
        data = [{
            "Mission ID": m.mission_id,
            "Name": m.name,
            "Type": m.mission_type,
            "Priority": m.priority,
            "Status": m.status,
            "Destination": m.destination,
            "Personnel": m.personnel_count
        } for m in missions]
        
    elif report_type.lower() == "request":
        requests = db.query(AssetRequest).all()
        data = [{
            "Request ID": r.request_id,
            "Mission": r.mission.name if r.mission else "N/A",
            "Asset": r.asset.name if r.asset else "N/A",
            "Status": r.status,
            "Priority": r.priority,
            "Requester": r.requested_by.full_name if r.requested_by else "N/A"
        } for r in requests]
        
    elif report_type.lower() == "maintenance":
        records = db.query(MaintenanceRecord).all()
        data = [{
            "Record ID": m.record_id,
            "Asset": m.asset.name if m.asset else "N/A",
            "Service Type": m.service_type,
            "Description": m.description,
            "Condition Before": m.condition_before,
            "Condition After": m.condition_after,
            "Status": m.status
        } for m in records]
        
    elif report_type.lower() == "inventory":
        items = db.query(InventoryItem).all()
        data = [{
            "Code": i.item_code,
            "Name": i.name,
            "Category": i.category,
            "Quantity": f"{i.quantity} {i.unit}",
            "Reorder Level": i.reorder_level,
            "Status": i.status,
            "Location": i.location
        } for i in items]
        
    if file_format.upper() == "PDF":
        filepath = generate_pdf_report(report_type, data, title)
        return FileResponse(filepath, media_type="application/pdf", filename=f"{report_type}_report.pdf")
    elif file_format.upper() == "XLSX":
        filepath = generate_excel_report(report_type, data, title)
        return FileResponse(filepath, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", filename=f"{report_type}_report.xlsx")
    else:
        filepath = generate_csv_report(report_type, data)
        return FileResponse(filepath, media_type="text/csv", filename=f"{report_type}_report.csv")
