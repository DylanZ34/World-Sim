#!/usr/bin/env python3
"""World restart script with agenda generation."""

import json
import random
import shutil
import subprocess
import sys
from datetime import datetime, UTC
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE_PATH = ROOT / "world" / "world-state.json"
TURN_LOG_DIR = ROOT / "world" / "turn-log"
ARCHIVE_DIR = ROOT / "archive"
SCRIPT_DIR = ROOT / "scripts"


def now_iso():
    return datetime.now(UTC).isoformat()


# Nation agenda pools (weighted by character fit)
AGENDA_POOLS = {
    "nation_1": [  # Hodges - civic/trade oriented
        {"id": "civic_prosperity", "name": "Civic Prosperity", "description": "Build the happiest nation", "weight": 40},
        {"id": "trade_empire", "name": "Trade Empire", "description": "Wealth through commerce", "weight": 30},
        {"id": "diplomatic_victory", "name": "Diplomatic Victory", "description": "Win through alliances", "weight": 30},
    ],
    "nation_2": [  # Aksum - merchant traders
        {"id": "trade_empire", "name": "Trade Empire", "description": "Wealth through trade", "weight": 40},
        {"id": "population_boom", "name": "Population Boom", "description": "Grow the merchant cities", "weight": 30},
        {"id": "cultural_dominance", "name": "Cultural Dominance", "description": "Spread trade influence", "weight": 30},
    ],
    "nation_3": [  # Urartu - fortress/military
        {"id": "military_might", "name": "Military Might", "description": "Build unstoppable army", "weight": 40},
        {"id": "world_conquest", "name": "World Conquest", "description": "Total domination", "weight": 30},
        {"id": "defensive_empire", "name": "Defensive Empire", "description": "Impenetrable defenses", "weight": 30},
    ],
}


def generate_agenda(nation_id: str) -> dict:
    """Generate random agenda fitting nation character."""
    pool = AGENDA_POOLS.get(nation_id, AGENDA_POOLS["nation_1"])
    total_weight = sum(p["weight"] for p in pool)
    r = random.randint(1, total_weight)
    cumulative = 0
    for agenda in pool:
        cumulative += agenda["weight"]
        if r <= cumulative:
            return agenda
    return pool[0]


def generate_map(num_cities: int = 10):
    """Generate world map."""
    print(f"  Generating map: {num_cities} cities...")
    result = subprocess.run(
        ["python3", str(SCRIPT_DIR / "generate_map.py"), str(num_cities)],
        capture_output=True, text=True, cwd=ROOT
    )
    if result.returncode != 0:
        print(f"  ! Map generation failed")
        return False
    
    result = subprocess.run(
        ["python3", str(SCRIPT_DIR / "visualize_map.py")],
        capture_output=True, text=True, cwd=ROOT
    )
    if result.returncode != 0:
        print(f"  ! PNG generation failed")
        return False
    
    print(f"  ✓ Map generated: {num_cities} cities")
    return True


def create_state_with_agenda() -> dict:
    """Create fresh world state with assigned agendas."""
    # Generate agendas
    agendas = {
        "nation_1": generate_agenda("nation_1"),
        "nation_2": generate_agenda("nation_2"),
        "nation_3": generate_agenda("nation_3"),
    }
    
    # Build state
    return {
        "turn": 1,
        "status": "ready",
        "turnOrder": ["nation_1", "nation_2", "nation_3"],
        "nations": [
            {"id": "nation_1", "agenda": agendas["nation_1"], "treasury": 6, "force": 4, "food": 6, "stability": 7, "industry": 6,
             "relationships": {"nation_2": 1, "nation_3": 0}},
            {"id": "nation_2", "agenda": agendas["nation_2"], "treasury": 7, "force": 5, "food": 5, "stability": 6, "industry": 6,
             "relationships": {"nation_1": 1, "nation_3": 0}},
            {"id": "nation_3", "agenda": agendas["nation_3"], "treasury": 5, "force": 7, "food": 6, "stability": 7, "industry": 5,
             "relationships": {"nation_1": 0, "nation_2": 0}},
        ],
        "treaties": [], "wars": [],
        "publicEvents": ["The world enters its first monitored turn under judge supervision."],
        "updatedAt": now_iso()
    }


def main():
    random.seed()
    num_cities = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    
    # Archive
    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    archive_path = ARCHIVE_DIR / f"world_{timestamp}"
    archive_path.mkdir(parents=True, exist_ok=True)
    
    print(f"=== World Restart ===")
    print(f"Archiving to: {archive_path}")
    
    # Archive state
    if STATE_PATH.exists():
        shutil.copy(STATE_PATH, archive_path / "world-state.json")
    
    # Archive logs
    if TURN_LOG_DIR.exists():
        dest = archive_path / "turn-log"
        dest.mkdir(parents=True, exist_ok=True)
        for f in TURN_LOG_DIR.glob("turn-*.json"):
            shutil.copy(f, dest / f.name)
    
    # Clear logs
    for f in TURN_LOG_DIR.glob("turn-*.json"):
        f.unlink()
    
    # Create state with agendas
    fresh_state = create_state_with_agenda()
    STATE_PATH.write_text(json.dumps(fresh_state, indent=2) + "\n")
    print(f"  ✓ Reset to turn 1 with agendas")
    
    # Generate map
    generate_map(num_cities)
    
    # Show agendas
    print(f"\nNations' Agendas:")
    for n in fresh_state["nations"]:
        print(f"  {n['id']}: {n['agenda']['name']} - {n['agenda']['description']}")
    
    print(f"\n=== World reset complete ===")
    print(f"Starting fresh from Turn 1 with {num_cities}-city map and agendas")


if __name__ == "__main__":
    main()