from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.models.asset import Asset
from app.models.mission import Mission
RECOMMENDATION_RULES: Dict[str, Dict[str, Any]] = {
    "Medical": {
        "preferred_types": ["Ambulance", "Medical Truck", "Mobile Field Hospital"],
        "min_fuel": 50.0,
        "min_battery": 50.0,
        "description": "Requires rapid medical transport equipped with life-support telemetry."
    },
    "Rescue": {
        "preferred_types": ["Helicopter", "Rescue Boat", "All-Terrain Rescue Vehicle"],
        "min_fuel": 60.0,
        "min_battery": 60.0,
        "description": "Requires amphibious or aerial extraction capabilities for high-hazard environments."
    },
    "Border Security": {
        "preferred_types": ["Armored Vehicle", "Patrol Drone", "Reconnaissance Vehicle"],
        "min_fuel": 50.0,
        "min_battery": 50.0,
        "description": "Requires heavy armor or surveillance equipment for perimeter border defense."
    },
    "Patrol": {
        "preferred_types": ["Armored Vehicle", "Light Utility Vehicle", "Patrol SUV"],
        "min_fuel": 40.0,
        "min_battery": 40.0,
        "description": "Standard ground reconnaissance and security patrol configuration."
    },
    "Logistics": {
        "preferred_types": ["Supply Truck", "Transport Truck", "Heavy Cargo Hauler"],
        "min_fuel": 40.0,
        "min_battery": 40.0,
        "description": "High payload cargo transport optimized for heavy supply chains."
    },
    "Training": {
        "preferred_types": ["Transport Truck", "Light Utility Vehicle", "Simulation Rig"],
        "min_fuel": 30.0,
        "min_battery": 30.0,
        "description": "Standard instructional vehicle configuration for cadet maneuvers."
    }
}
def recommend_assets_for_mission(db: Session, mission_id: int) -> Dict[str, Any]:
    mission = db.query(Mission).filter(Mission.id == mission_id).first()
    if not mission:
        return {"error": "Mission not found", "recommendations": []}
    
    rule = RECOMMENDATION_RULES.get(mission.mission_type, {
        "preferred_types": ["Light Utility Vehicle", "Transport Truck"],
        "min_fuel": 30.0,
        "min_battery": 30.0,
        "description": "General purpose military utility configuration."
    })
