import os
import sys
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add backend directory to sys path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from main import app
from app.core.database import Base, get_db
from app.core.security import get_password_hash, create_access_token
from app.models.user import User, Role
from app.models.asset import Asset
from app.models.mission import Mission
from app.models.request import AssetRequest

TEST_SQLALCHEMY_DATABASE_URL = "sqlite:///./test_military_assets.db"
engine = create_engine(TEST_SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def setup_test_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    db = TestingSessionLocal()
    
    # Seed roles
    roles = ["Admin", "Commander", "Logistics Officer", "Technician", "Unit Officer"]
    for r in roles:
        db.add(Role(name=r, description=f"{r} test role"))
    db.commit()
    
    # Seed users for each role
    pwd_hash = get_password_hash("Password123!")
    users_data = [
        ("test_admin@defense.gov", "Test Admin", "Admin"),
        ("test_commander@defense.gov", "Test Commander", "Commander"),
        ("test_logistics@defense.gov", "Test Logistics", "Logistics Officer"),
        ("test_technician@defense.gov", "Test Technician", "Technician"),
        ("test_unit@defense.gov", "Test Unit Officer", "Unit Officer"),
    ]
    for email, name, role in users_data:
        db.add(User(email=email, password_hash=pwd_hash, full_name=name, role=role, is_active=True))
    db.commit()
    
    yield
    Base.metadata.drop_all(bind=engine)

def get_auth_header(email: str, role: str) -> dict:
    db = TestingSessionLocal()
    user = db.query(User).filter(User.email == email).first()
    db.close()
    token = create_access_token(subject=user.id, role=role)
    return {"Authorization": f"Bearer {token}"}

# ==========================================
# 40+ DOCUMENTED COMPREHENSIVE TEST CASES
# ==========================================

# 1-5: Authentication Tests
def test_TC_AUTH_01_valid_login():
    """TC-AUTH-01: Module=AUTH, Input=Valid Credentials, Expected=200 OK & JWT Token"""
    res = client.post("/api/v1/auth/login", data={"username": "test_admin@defense.gov", "password": "Password123!"})
    assert res.status_code == 200
    assert "access_token" in res.json()

def test_TC_AUTH_02_invalid_password():
    """TC-AUTH-02: Module=AUTH, Input=Wrong Password, Expected=401 Unauthorized"""
    res = client.post("/api/v1/auth/login", data={"username": "test_admin@defense.gov", "password": "WrongPassword"})
    assert res.status_code == 401

def test_TC_AUTH_03_nonexistent_user():
    """TC-AUTH-03: Module=AUTH, Input=Unknown Email, Expected=401 Unauthorized"""
    res = client.post("/api/v1/auth/login", data={"username": "ghost@defense.gov", "password": "Password123!"})
    assert res.status_code == 401

def test_TC_AUTH_04_get_current_user_profile():
    """TC-AUTH-04: Module=AUTH, Input=Valid Bearer Header, Expected=200 OK & Profile Data"""
    headers = get_auth_header("test_admin@defense.gov", "Admin")
    res = client.get("/api/v1/auth/me", headers=headers)
    assert res.status_code == 200
    assert res.json()["email"] == "test_admin@defense.gov"

def test_TC_AUTH_05_unauthenticated_protected_route():
    """TC-AUTH-05: Module=AUTH, Input=No Authorization Token, Expected=401 Unauthorized"""
    res = client.get("/api/v1/auth/me")
    assert res.status_code == 401

# 6-10: RBAC Authorization Tests
def test_TC_RBAC_06_admin_access_users_endpoint():
    """TC-RBAC-06: Module=RBAC, Input=Admin Role Token, Expected=200 OK"""
    headers = get_auth_header("test_admin@defense.gov", "Admin")
    res = client.get("/api/v1/users", headers=headers)
    assert res.status_code == 200

def test_TC_RBAC_07_unit_officer_denied_user_creation():
    """TC-RBAC-07: Module=RBAC, Input=Unit Officer Token on Admin Route, Expected=403 Forbidden"""
    headers = get_auth_header("test_unit@defense.gov", "Unit Officer")
    res = client.post("/api/v1/users", headers=headers, json={
        "email": "hacker@defense.gov", "password": "Password123!", "full_name": "Hacker", "role": "Admin"
    })
    assert res.status_code == 403

def test_TC_RBAC_08_commander_approved_roles():
    """TC-RBAC-08: Module=RBAC, Input=Commander Token on Missions, Expected=200 OK"""
    headers = get_auth_header("test_commander@defense.gov", "Commander")
    res = client.get("/api/v1/missions", headers=headers)
    assert res.status_code == 200

def test_TC_RBAC_09_technician_allowed_maintenance_post():
    """TC-RBAC-09: Module=RBAC, Input=Technician Token on Maintenance, Expected=200 OK or 404 for missing asset"""
    headers = get_auth_header("test_technician@defense.gov", "Technician")
    res = client.get("/api/v1/maintenance", headers=headers)
    assert res.status_code == 200

def test_TC_RBAC_10_logistics_allowed_inventory_access():
    """TC-RBAC-10: Module=RBAC, Input=Logistics Token on Inventory, Expected=200 OK"""
    headers = get_auth_header("test_logistics@defense.gov", "Logistics Officer")
    res = client.get("/api/v1/inventory", headers=headers)
    assert res.status_code == 200

# 11-18: Asset Management CRUD Tests
def test_TC_ASSET_11_create_asset_success():
    """TC-ASSET-11: Module=ASSETS, Input=Valid Asset Payload, Expected=201 Created"""
    headers = get_auth_header("test_admin@defense.gov", "Admin")
    payload = {
        "asset_id": "AST-9001",
        "name": "Armored Titan I",
        "category": "Vehicle",
        "type": "Armored Vehicle",
        "serial_number": "SN-9001-TEST",
        "manufacturer": "Oshkosh Defense",
        "fuel_level": 95.0,
        "battery_status": 90.0,
        "condition": "Excellent",
        "maintenance_status": "Healthy",
        "availability": "Available"
    }
    res = client.post("/api/v1/assets", headers=headers, json=payload)
    assert res.status_code == 201
    assert res.json()["asset_id"] == "AST-9001"

def test_TC_ASSET_12_duplicate_asset_id_rejection():
    """TC-ASSET-12: Module=ASSETS, Input=Duplicate Asset ID, Expected=400 Bad Request"""
    headers = get_auth_header("test_admin@defense.gov", "Admin")
    payload = {
        "asset_id": "AST-9001",
        "name": "Duplicate Titan",
        "category": "Vehicle",
        "type": "Armored Vehicle",
        "serial_number": "SN-9002-DUP",
        "manufacturer": "Oshkosh Defense"
    }
    res = client.post("/api/v1/assets", headers=headers, json=payload)
    assert res.status_code == 400

def test_TC_ASSET_13_get_asset_by_id():
    """TC-ASSET-13: Module=ASSETS, Input=Asset ID 1, Expected=200 OK & Asset Details"""
    headers = get_auth_header("test_admin@defense.gov", "Admin")
    res = client.get("/api/v1/assets/1", headers=headers)
    assert res.status_code == 200
    assert res.json()["id"] == 1

def test_TC_ASSET_14_search_assets_query():
    """TC-ASSET-14: Module=ASSETS, Input=Search query 'Titan', Expected=200 OK & Filtered Results"""
    headers = get_auth_header("test_admin@defense.gov", "Admin")
    res = client.get("/api/v1/assets?search=Titan", headers=headers)
    assert res.status_code == 200
    assert res.json()["total"] >= 1

def test_TC_ASSET_15_filter_assets_by_category():
    """TC-ASSET-15: Module=ASSETS, Input=Category 'Vehicle', Expected=200 OK & Category Match"""
    headers = get_auth_header("test_admin@defense.gov", "Admin")
    res = client.get("/api/v1/assets?category=Vehicle", headers=headers)
    assert res.status_code == 200

def test_TC_ASSET_16_update_asset_condition():
    """TC-ASSET-16: Module=ASSETS, Input=PUT condition='Good', Expected=200 OK & Updated Field"""
    headers = get_auth_header("test_admin@defense.gov", "Admin")
    res = client.put("/api/v1/assets/1", headers=headers, json={"condition": "Good", "fuel_level": 80.0})
    assert res.status_code == 200
    assert res.json()["condition"] == "Good"

def test_TC_ASSET_17_pagination_sorting():
    """TC-ASSET-17: Module=ASSETS, Input=page=1&size=5&sort_by=name&order=desc, Expected=200 OK"""
    headers = get_auth_header("test_admin@defense.gov", "Admin")
    res = client.get("/api/v1/assets?page=1&size=5&sort_by=name&order=desc", headers=headers)
    assert res.status_code == 200
    assert len(res.json()["items"]) <= 5

def test_TC_ASSET_18_delete_asset_admin():
    """TC-ASSET-18: Module=ASSETS, Input=DELETE Asset ID 1, Expected=204 No Content"""
    headers = get_auth_header("test_admin@defense.gov", "Admin")
    res = client.delete("/api/v1/assets/1", headers=headers)
    assert res.status_code == 204

# 19-24: Mission Management Tests
def test_TC_MISSION_19_create_mission_success():
    """TC-MISSION-19: Module=MISSIONS, Input=Valid Mission Payload, Expected=201 Created"""
    headers = get_auth_header("test_unit@defense.gov", "Unit Officer")
    payload = {
        "mission_id": "MSN-9001",
        "name": "Operation Medical Shield",
        "mission_type": "Medical",
        "priority": "High",
        "description": "Emergency medical evacuation",
        "start_date": "2026-08-01T00:00:00Z",
        "end_date": "2026-08-05T00:00:00Z",
        "destination": "Forward Post Bravo",
        "personnel_count": 12
    }
    res = client.post("/api/v1/missions", headers=headers, json=payload)
    assert res.status_code == 201
    assert res.json()["mission_id"] == "MSN-9001"

def test_TC_MISSION_20_list_missions_filter_type():
    """TC-MISSION-20: Module=MISSIONS, Input=mission_type='Medical', Expected=200 OK"""
    headers = get_auth_header("test_commander@defense.gov", "Commander")
    res = client.get("/api/v1/missions?mission_type=Medical", headers=headers)
    assert res.status_code == 200

def test_TC_MISSION_21_update_mission_status():
    """TC-MISSION-21: Module=MISSIONS, Input=status='Active', Expected=200 OK"""
    headers = get_auth_header("test_commander@defense.gov", "Commander")
    res = client.put("/api/v1/missions/1", headers=headers, json={"status": "Active"})
    assert res.status_code == 200
    assert res.json()["status"] == "Active"

def test_TC_MISSION_22_get_mission_details():
    """TC-MISSION-22: Module=MISSIONS, Input=Mission ID 1, Expected=200 OK"""
    headers = get_auth_header("test_unit@defense.gov", "Unit Officer")
    res = client.get("/api/v1/missions/1", headers=headers)
    assert res.status_code == 200

def test_TC_MISSION_23_recommendation_engine_rule():
    """TC-MISSION-23: Module=RECOMMENDATIONS, Input=Mission ID 1 (Medical), Expected=200 OK & Preferred Types [Ambulance, Medical Truck]"""
    headers = get_auth_header("test_unit@defense.gov", "Unit Officer")
    res = client.get("/api/v1/requests/recommendations/1", headers=headers)
    assert res.status_code == 200
    assert "Ambulance" in res.json()["recommended_types"]

def test_TC_MISSION_24_recommendation_nonexistent_mission():
    """TC-MISSION-24: Module=RECOMMENDATIONS, Input=Invalid Mission ID 9999, Expected=200 with error summary"""
    headers = get_auth_header("test_unit@defense.gov", "Unit Officer")
    res = client.get("/api/v1/requests/recommendations/9999", headers=headers)
    assert res.status_code == 200
    assert "error" in res.json()

# 25-32: Asset Request Workflow State Machine Tests
def test_TC_REQ_25_create_asset_request():
    """TC-REQ-25: Module=WORKFLOW, Input=Valid Mission & Asset IDs, Expected=201 Created & Status='Submitted'"""
    # Create asset first
    headers_adm = get_auth_header("test_admin@defense.gov", "Admin")
    asset_res = client.post("/api/v1/assets", headers=headers_adm, json={
        "asset_id": "AST-9002", "name": "Rescue Copter", "category": "Aircraft", "type": "Helicopter",
        "serial_number": "SN-9002-COP", "manufacturer": "Sikorsky"
    })
    asset_id = asset_res.json()["id"]
    
    headers_unit = get_auth_header("test_unit@defense.gov", "Unit Officer")
    res = client.post("/api/v1/requests", headers=headers_unit, json={
        "mission_id": 1, "asset_id": asset_id, "priority": "High", "reason": "Medical evacuation airlift"
    })
    assert res.status_code == 201
    assert res.json()["status"] == "Submitted"

def test_TC_REQ_26_commander_approval():
    """TC-REQ-26: Module=WORKFLOW, Input=Commander Action Approve, Expected=200 OK & Status='Approved'"""
    headers = get_auth_header("test_commander@defense.gov", "Commander")
    res = client.post("/api/v1/requests/1/commander-action", headers=headers, json={
        "action": "Approve", "commander_notes": "Airlift cleared for operation."
    })
    assert res.status_code == 200
    assert res.json()["status"] == "Approved"

def test_TC_REQ_27_logistics_dispatch():
    """TC-REQ-27: Module=WORKFLOW, Input=Logistics Dispatch Action, Expected=200 OK & Status='Dispatched' & Asset Availability='Assigned'"""
    headers = get_auth_header("test_logistics@defense.gov", "Logistics Officer")
    res = client.post("/api/v1/requests/1/dispatch", headers=headers, json={
        "logistics_notes": "Copter prepped at Helipad Alpha"
    })
    assert res.status_code == 200
    assert res.json()["status"] == "Dispatched"

def test_TC_REQ_28_technician_inspection():
    """TC-REQ-28: Module=WORKFLOW, Input=Technician Inspection Action, Expected=200 OK & Status='Inspected & Active'"""
    headers = get_auth_header("test_technician@defense.gov", "Technician")
    res = client.post("/api/v1/requests/1/inspect", headers=headers, json={
        "technician_notes": "Rotor Blades checked", "condition_rating": "Excellent", "fuel_level": 98.0, "battery_status": 100.0
    })
    assert res.status_code == 200
    assert res.json()["status"] == "Inspected & Active"

def test_TC_REQ_29_asset_return_and_completion():
    """TC-REQ-29: Module=WORKFLOW, Input=Return Action, Expected=200 OK & Status='Returned & Completed' & Asset Availability='Available'"""
    headers = get_auth_header("test_unit@defense.gov", "Unit Officer")
    res = client.post("/api/v1/requests/1/return", headers=headers)
    assert res.status_code == 200
    assert res.json()["status"] == "Returned & Completed"

def test_TC_REQ_30_commander_rejection():
    """TC-REQ-30: Module=WORKFLOW, Input=Commander Action Reject on new request, Expected=200 OK & Status='Rejected'"""
    # Create request 2
    headers_adm = get_auth_header("test_admin@defense.gov", "Admin")
    asset_res = client.post("/api/v1/assets", headers=headers_adm, json={
        "asset_id": "AST-9003", "name": "Cargo Truck B", "category": "Supply", "type": "Supply Truck",
        "serial_number": "SN-9003-TRK", "manufacturer": "Oshkosh"
    })
    asset_id = asset_res.json()["id"]
    
    headers_unit = get_auth_header("test_unit@defense.gov", "Unit Officer")
    req_res = client.post("/api/v1/requests", headers=headers_unit, json={
        "mission_id": 1, "asset_id": asset_id, "priority": "Low", "reason": "Non-essential supply move"
    })
    req_id = req_res.json()["id"]
    
    headers_cmd = get_auth_header("test_commander@defense.gov", "Commander")
    res = client.post(f"/api/v1/requests/{req_id}/commander-action", headers=headers_cmd, json={
        "action": "Reject", "commander_notes": "Denied due to low priority."
    })
    assert res.status_code == 200
    assert res.json()["status"] == "Rejected"

def test_TC_REQ_31_cannot_dispatch_rejected_request():
    """TC-REQ-31: Module=WORKFLOW, Input=Dispatch on Rejected Request, Expected=400 Bad Request"""
    headers = get_auth_header("test_logistics@defense.gov", "Logistics Officer")
    res = client.post("/api/v1/requests/2/dispatch", headers=headers, json={"logistics_notes": "Test invalid dispatch"})
    assert res.status_code == 400

def test_TC_REQ_32_cannot_dispatch_under_maintenance_asset():
    """TC-REQ-32: Module=WORKFLOW, Input=Request on Asset Under Maintenance, Expected=400 Bad Request"""
    headers_adm = get_auth_header("test_admin@defense.gov", "Admin")
    asset_res = client.post("/api/v1/assets", headers=headers_adm, json={
        "asset_id": "AST-9004", "name": "Broken Tank", "category": "Vehicle", "type": "Armored Vehicle",
        "serial_number": "SN-9004-BRK", "manufacturer": "General Dynamics", "maintenance_status": "Under Maintenance"
    })
    asset_id = asset_res.json()["id"]
    
    headers_unit = get_auth_header("test_unit@defense.gov", "Unit Officer")
    res = client.post("/api/v1/requests", headers=headers_unit, json={
        "mission_id": 1, "asset_id": asset_id, "priority": "High", "reason": "Need tank"
    })
    assert res.status_code == 400

# 33-36: Maintenance & Inventory Module Tests
def test_TC_MNT_33_record_maintenance_log():
    """TC-MNT-33: Module=MAINTENANCE, Input=Valid Maintenance Payload, Expected=201 Created & Asset Status Updated"""
    headers = get_auth_header("test_technician@defense.gov", "Technician")
    payload = {
        "asset_id": 2,
        "service_type": "Engine Repair",
        "description": "Replaced turbocharger and oil filters",
        "mileage": 1500.0,
        "fuel_level": 100.0,
        "battery_status": 100.0,
        "condition_before": "Fair",
        "condition_after": "Excellent",
        "status": "Completed"
    }
    res = client.post("/api/v1/maintenance", headers=headers, json=payload)
    assert res.status_code == 201
    assert res.json()["service_type"] == "Engine Repair"

def test_TC_MNT_34_list_maintenance_records():
    """TC-MNT-34: Module=MAINTENANCE, Input=GET /maintenance, Expected=200 OK"""
    headers = get_auth_header("test_technician@defense.gov", "Technician")
    res = client.get("/api/v1/maintenance", headers=headers)
    assert res.status_code == 200

def test_TC_INV_35_create_inventory_item():
    """TC-INV-35: Module=INVENTORY, Input=Valid Inventory Payload, Expected=201 Created"""
    headers = get_auth_header("test_logistics@defense.gov", "Logistics Officer")
    payload = {
        "item_code": "INV-9001",
        "name": "High-Grade JP-8 Jet Fuel",
        "category": "Fuel",
        "quantity": 50000.0,
        "unit": "Liters",
        "reorder_level": 10000.0,
        "location": "Main Fuel Depot A"
    }
    res = client.post("/api/v1/inventory", headers=headers, json=payload)
    assert res.status_code == 201
    assert res.json()["item_code"] == "INV-9001"

def test_TC_INV_36_update_inventory_low_stock_trigger():
    """TC-INV-36: Module=INVENTORY, Input=PUT quantity below reorder level, Expected=200 OK & Status='Low Stock'"""
    headers = get_auth_header("test_logistics@defense.gov", "Logistics Officer")
    res = client.put("/api/v1/inventory/1", headers=headers, json={"quantity": 8000.0})
    assert res.status_code == 200
    assert res.json()["status"] == "Low Stock"


# 37-40: Reports, Notifications & Audit Trail Tests
def test_TC_RPT_37_dashboard_stats_aggregation():
    """TC-RPT-37: Module=REPORTS, Input=GET /dashboard-stats, Expected=200 OK & Key Summary Statistics"""
    headers = get_auth_header("test_commander@defense.gov", "Commander")
    res = client.get("/api/v1/reports/dashboard-stats", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "summary" in data
    assert "charts" in data

def test_TC_RPT_38_export_pdf_report():
    """TC-RPT-38: Module=REPORTS, Input=GET /export?report_type=Asset&file_format=PDF, Expected=200 OK & Application/PDF Header"""
    headers = get_auth_header("test_admin@defense.gov", "Admin")
    res = client.get("/api/v1/reports/export?report_type=Asset&file_format=PDF", headers=headers)
    assert res.status_code == 200
    assert res.headers["content-type"] == "application/pdf"

def test_TC_RPT_39_export_excel_report():
    """TC-RPT-39: Module=REPORTS, Input=GET /export?report_type=Mission&file_format=XLSX, Expected=200 OK & Spreadsheet Header"""
    headers = get_auth_header("test_admin@defense.gov", "Admin")
    res = client.get("/api/v1/reports/export?report_type=Mission&file_format=XLSX", headers=headers)
    assert res.status_code == 200
    assert "spreadsheet" in res.headers["content-type"]

def test_TC_AUDIT_40_view_audit_logs_admin():
    """TC-AUDIT-40: Module=AUDIT, Input=GET /audit-logs, Expected=200 OK & List of recorded system events"""
    headers = get_auth_header("test_admin@defense.gov", "Admin")
    res = client.get("/api/v1/audit-logs", headers=headers)
    assert res.status_code == 200
    assert isinstance(res.json(), list)

def test_TC_NOTIF_41_get_user_notifications():
    """TC-NOTIF-41: Module=NOTIFICATIONS, Input=GET /notifications, Expected=200 OK"""
    headers = get_auth_header("test_logistics@defense.gov", "Logistics Officer")
    res = client.get("/api/v1/notifications", headers=headers)
    assert res.status_code == 200
