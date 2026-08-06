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
    
    # Query available assets matching conditions
    available_assets = db.query(Asset).filter(
        Asset.availability == "Available",
        Asset.maintenance_status == "Healthy",
        Asset.fuel_level >= rule["min_fuel"],
        Asset.battery_status >= rule["min_battery"]
    ).all()
    
    scored_recommendations = []
    for asset in available_assets:
        score = 50.0 # Base score
        matched_rule = False
        
        if asset.type in rule["preferred_types"]:
            score += 40.0
            matched_rule = True
            
        # Fuel & Battery Bonus
        score += (asset.fuel_level * 0.05) + (asset.battery_status * 0.05)
        
        # Priority boost for high condition
        if asset.condition == "Excellent":
            score += 10.0
        elif asset.condition == "Good":
            score += 5.0
            
        scored_recommendations.append({
            "asset_id": asset.id,
            "asset_code": asset.asset_id,
            "name": asset.name,
            "category": asset.category,
            "type": asset.type,
            "fuel_level": asset.fuel_level,
            "battery_status": asset.battery_status,
            "condition": asset.condition,
            "current_location": asset.current_location,
            "match_score": round(score, 1),
            "is_ideal_match": matched_rule,
            "reason": f"Type '{asset.type}' meets mission '{mission.mission_type}' criteria with {asset.fuel_level}% fuel."
        })
        
    # Sort by match score descending
    scored_recommendations.sort(key=lambda x: x["match_score"], reverse=True)
    
    return {
        "mission_id": mission.id,
        "mission_name": mission.name,
        "mission_type": mission.mission_type,
        "rule_applied": rule["description"],
        "recommended_types": rule["preferred_types"],
        "total_available_candidates": len(available_assets),
        "recommendations": scored_recommendations[:10] # Top 10 recommendations
    }
