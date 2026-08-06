import random
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine, Base
from app.core.security import get_password_hash
from app.models.user import User, Role
from app.models.asset import Asset
from app.models.mission import Mission
from app.models.request import AssetRequest
from app.models.maintenance import MaintenanceRecord
from app.models.inventory import InventoryItem
from app.models.notification import Notification
from app.models.audit import AuditLog

ROLES_LIST = [
    {"name": "Admin", "description": "Full system access, user management, audit logs, reports"},
    {"name": "Commander", "description": "View missions, approve/reject requests, command dashboard"},
    {"name": "Logistics Officer", "description": "Dispatch assets, delivery tracking, inventory management"},
    {"name": "Technician", "description": "Maintenance updates, asset health logs, technical inspections"},
    {"name": "Unit Officer", "description": "Create missions, asset requests, view assigned unit assets"}
]

CATEGORIES_TYPES = {
    "Vehicle": ["Armored Vehicle", "Transport Truck", "Ambulance", "Patrol SUV", "Light Utility Vehicle"],
    "Aircraft": ["Helicopter", "Reconnaissance Drone", "Cargo Transport Aircraft"],
    "Maritime": ["Rescue Boat", "Patrol Gunboat", "Tactical Inflatable Vessel"],
    "Communications": ["Mobile Comms Rig", "Satellite Relay Station", "Tactical Radio Command"],
    "Medical": ["Mobile Field Hospital", "Medical Truck", "Emergency Trauma Unit"],
    "Supply": ["Heavy Cargo Hauler", "Supply Truck", "Fuel Tanker Truck"]
}

UNITS_LIST = [
    "1st Armored Division", "7th Tactical Air Command", "3rd Rapid Response Brigade",
    "5th Border Recon Force", "Logistics Support Command", "Medical Corps Alpha"
]

LOCATIONS_LIST = [
    "Base Depot Alpha", "Forward Operating Base Bravo", "Northern Border Checkpoint 4",
    "Coast Guard Harbor Station", "Central Airfield Hangar 3", "Southern Command Post"
]

def seed_database():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    try:
        # Check if already seeded
        if db.query(User).count() >= 20:
            print("Database already seeded with demo data!")
            return
            
        print("Seeding database with demo data...")
        
        # 1. Seed Roles
        role_objs = {}
        for r in ROLES_LIST:
            existing = db.query(Role).filter(Role.name == r["name"]).first()
            if not existing:
                existing = Role(**r)
                db.add(existing)
                db.flush()
            role_objs[r["name"]] = existing
            
        # 2. Seed 20 Users across all 5 roles
        default_pwd = get_password_hash("Password123!")
        users = []
        
        # Core standard logins
        users_specs = [
            ("admin@defense.gov", "General Alexander Vance", "Admin", "High Command", "General", "MIL-ADM-001"),
            ("commander@defense.gov", "Col. Marcus Sterling", "Commander", "1st Armored Division", "Colonel", "MIL-CMD-002"),
            ("logistics@defense.gov", "Maj. Sarah Jenkins", "Logistics Officer", "Logistics Support Command", "Major", "MIL-LOG-003"),
            ("technician@defense.gov", "Chief Sgt. David Miller", "Technician", "Base Depot Alpha", "Chief Sergeant", "MIL-TEC-004"),
            ("unit@defense.gov", "Capt. James Rodriguez", "Unit Officer", "3rd Rapid Response Brigade", "Captain", "MIL-UNT-005")
        ]
        
        for email, name, role, unit, rank, service_id in users_specs:
            u = User(
                email=email,
                password_hash=default_pwd,
                full_name=name,
                role=role,
                role_id=role_objs[role].id,
                unit=unit,
                rank=rank,
                service_id=service_id,
                is_active=True
            )
            db.add(u)
            users.append(u)
            
        # Generate remaining 15 users
        roles_pool = ["Commander", "Logistics Officer", "Technician", "Unit Officer"]
        ranks_pool = ["Captain", "Lieutenant", "Sergeant", "Staff Sergeant", "Major"]
        first_names = ["Robert", "Elena", "Viktor", "Sophia", "Daniel", "Amara", "Lucas", "Maya", "Ethan", "Nadia", "Carlos", "Tanya", "Oliver", "Zoe", "Liam"]
        last_names = ["Chen", "Kovalenko", "Patel", "Dubois", "O'Connor", "Santos", "Novak", "Takahashi", "Gomez", "Muller", "Sinclair", "Al-Mansoor", "Zhao", "Wojcik", "Brahma"]
        
        for i in range(15):
            role_choice = roles_pool[i % len(roles_pool)]
            fn = first_names[i]
            ln = last_names[i]
            u = User(
                email=f"{fn.lower()}.{ln.lower()}@defense.gov",
                password_hash=default_pwd,
                full_name=f"{fn} {ln}",
                role=role_choice,
                role_id=role_objs[role_choice].id,
                unit=random.choice(UNITS_LIST),
                rank=random.choice(ranks_pool),
                service_id=f"MIL-SER-0{10 + i}",
                is_active=True
            )
            db.add(u)
            users.append(u)
            
        db.flush()
        print(f"Seeded {len(users)} users.")
        
        # 3. Seed 100 Assets
        assets = []
        asset_counter = 1001
        for cat, types in CATEGORIES_TYPES.items():
            for t in types:
                for idx in range(3): # ~18 types * 3-6 = 100 assets
                    a_code = f"AST-{asset_counter}"
                    asset_counter += 1
                    
                    fuel = round(random.uniform(35.0, 100.0), 1)
                    batt = round(random.uniform(40.0, 100.0), 1)
                    cond = random.choice(["Excellent", "Excellent", "Good", "Good", "Fair", "Needs Service"])
                    mnt_stat = "Healthy" if cond in ["Excellent", "Good"] else "Needs Service"
                    if random.random() < 0.1:
                        mnt_stat = "Under Maintenance"
                        cond = "Under Repair"
                        
                    avail = "Available"
                    if mnt_stat == "Under Maintenance":
                        avail = "Under Maintenance"
                    elif random.random() < 0.25:
                        avail = "In Mission"
                        
                    asset = Asset(
                        asset_id=a_code,
                        name=f"{t} {random.choice(['Alpha', 'Falcon', 'Vanguard', 'Titan', 'Apex', 'Sentinel'])}-{idx+1}",
                        category=cat,
                        type=t,
                        serial_number=f"SN-2026-{asset_counter:04d}-{random.randint(100, 999)}",
                        manufacturer=random.choice(["Oshkosh Defense", "Lockheed Martin", "General Dynamics", "BAE Systems", "Textron Systems"]),
                        purchase_date=datetime.now(timezone.utc) - timedelta(days=random.randint(100, 1500)),
                        fuel_level=fuel,
                        battery_status=batt,
                        mileage=round(random.uniform(120.0, 8500.0), 1),
                        condition=cond,
                        maintenance_status=mnt_stat,
                        availability=avail,
                        assigned_unit=random.choice(UNITS_LIST),
                        current_location=random.choice(LOCATIONS_LIST),
                        last_service_date=datetime.now(timezone.utc) - timedelta(days=random.randint(10, 180)),
                        next_service_date=datetime.now(timezone.utc) + timedelta(days=random.randint(15, 120))
                    )
                    db.add(asset)
                    assets.append(asset)
                    
        db.flush()
        print(f"Seeded {len(assets)} assets.")
        
        # 4. Seed 50 Missions
        missions = []
        mission_types = ["Patrol", "Rescue", "Medical", "Training", "Logistics", "Border Security"]
        priorities = ["Low", "Medium", "High", "Critical"]
        unit_officers = [u for u in users if u.role in ["Unit Officer", "Commander", "Admin"]]
        
        for i in range(50):
            m_code = f"MSN-2{100 + i + 1}"
            m_type = mission_types[i % len(mission_types)]
            prio = random.choice(priorities)
            stat = random.choice(["Planned", "Active", "Active", "Completed", "Completed"])
            
            start_dt = datetime.now(timezone.utc) - timedelta(days=random.randint(0, 30))
            end_dt = start_dt + timedelta(days=random.randint(2, 14))
            
            m = Mission(
                mission_id=m_code,
                name=f"Operation {m_type} {random.choice(['Shield', 'Storm', 'Thunder', 'Watch', 'Guardian', 'Pathfinder'])} {i+1}",
                mission_type=m_type,
                priority=prio,
                description=f"Tactical {m_type.lower()} maneuver covering sector {random.randint(1, 12)} with rapid response protocols.",
                start_date=start_dt,
                end_date=end_dt,
                destination=random.choice(LOCATIONS_LIST),
                personnel_count=random.randint(4, 45),
                status=stat,
                created_by_id=random.choice(unit_officers).id
            )
            db.add(m)
            missions.append(m)
            
        db.flush()
        print(f"Seeded {len(missions)} missions.")
        
        # 5. Seed 100 Asset Requests
        requests = []
        req_statuses = ["Submitted", "Approved", "Dispatched", "Inspected & Active", "Returned & Completed", "Rejected"]
        
        for i in range(100):
            r_code = f"REQ-3{100 + i + 1}"
            m_choice = random.choice(missions)
            a_choice = random.choice(assets)
            u_choice = random.choice(unit_officers)
            status_choice = req_statuses[i % len(req_statuses)]
            
            req = AssetRequest(
                request_id=r_code,
                mission_id=m_choice.id,
                asset_id=a_choice.id,
                requested_by_id=u_choice.id,
                status=status_choice,
                priority=random.choice(priorities),
                reason=f"Required for mission '{m_choice.name}' tactical support.",
                commander_notes="Approved for tactical deployment." if status_choice != "Submitted" else None,
                logistics_notes="Asset cleared for dispatch." if status_choice in ["Dispatched", "Inspected & Active", "Returned & Completed"] else None,
                technician_notes="Pre-flight safety inspection verified clean." if status_choice in ["Inspected & Active", "Returned & Completed"] else None,
                requested_at=datetime.now(timezone.utc) - timedelta(days=random.randint(1, 45))
            )
            db.add(req)
            requests.append(req)
            
        db.flush()
        print(f"Seeded {len(requests)} asset requests.")
        
        # 6. Seed Inventory Items
        inventory_data = [
            ("INV-5001", "JP-8 Aviation Fuel", "Fuel", 45000.0, "Liters", 10000.0, "Fuel Storage Tank A"),
            ("INV-5002", "Diesel Defense Grade", "Fuel", 8500.0, "Liters", 12000.0, "Fuel Storage Tank B"), # Low Stock
            ("INV-5003", "Combat Field Medical Kits", "Medical Kits", 450.0, "Units", 100.0, "Medical Depot Locker 1"),
            ("INV-5004", "Emergency Burn & Trauma Trauma Packs", "Medical Kits", 45.0, "Units", 50.0, "Medical Depot Locker 2"), # Low Stock
            ("INV-5005", "Encrypted Tactical VHF Radios", "Communication Devices", 120.0, "Units", 30.0, "Comms Vault 3"),
            ("INV-5006", "Satellite Field Comms Terminals", "Communication Devices", 18.0, "Units", 20.0, "Comms Vault 3"), # Low Stock
            ("INV-5007", "Heavy Vehicle Lithium Power Cells", "Batteries", 85.0, "Units", 25.0, "Battery Storage Hub"),
            ("INV-5008", "All-Terrain Run-Flat Tyres (Heavy)", "Tyres", 320.0, "Units", 80.0, "Motor Pool Shed 4"),
            ("INV-5009", "Heavy Armored Vehicle Brake Pads", "Repair Parts", 140.0, "Sets", 40.0, "Spare Parts Rack B"),
            ("INV-5010", "Helicopter Rotor Seal Repair Kits", "Repair Parts", 8.0, "Kits", 15.0, "Hangar Maintenance Shop") # Critical Stock
        ]
        
        for code, name, cat, qty, unit, reorder, loc in inventory_data:
            stat = "Sufficient"
            if qty <= reorder * 0.5:
                stat = "Critical Stock"
            elif qty <= reorder:
                stat = "Low Stock"
                
            inv = InventoryItem(
                item_code=code,
                name=name,
                category=cat,
                quantity=qty,
                unit=unit,
                reorder_level=reorder,
                location=loc,
                status=stat
            )
            db.add(inv)
            
        # 7. Seed 300 Audit Logs
        actions = ["USER_LOGIN", "ASSET_CREATED", "ASSET_UPDATED", "REQUEST_SUBMITTED", "REQUEST_APPROVED", "REQUEST_DISPATCHED", "MAINTENANCE_RECORDED", "INVENTORY_UPDATED"]
        modules = ["AUTH", "ASSETS", "REQUESTS", "MAINTENANCE", "INVENTORY", "MISSIONS"]
        
        for i in range(300):
            u = random.choice(users)
            act = random.choice(actions)
            mod = random.choice(modules)
            
            audit = AuditLog(
                user_id=u.id,
                user_name=u.full_name,
                user_role=u.role,
                action=act,
                module=mod,
                ip_address=f"192.168.1.{random.randint(10, 250)}",
                old_value=f'{{"status": "Pending", "iteration": {i}}}',
                new_value=f'{{"status": "Processed", "iteration": {i}}}',
                timestamp=datetime.now(timezone.utc) - timedelta(hours=random.randint(1, 720))
            )
            db.add(audit)
            
        db.commit()
        print("Demo database seeding complete!")
        
    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
