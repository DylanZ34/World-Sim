#!/usr/bin/env python3
"""World restart script.

Archives current state and logs, then resets to turn 1 fresh.

Usage:
    python3 restart_world.py
"""

import json
import shutil
import sys
from datetime import datetime, UTC
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE_PATH = ROOT / "world" / "world-state.json"
TURN_LOG_DIR = ROOT / "world" / "turn-log"
ARCHIVE_DIR = ROOT / "archive"


def now_iso():
    return datetime.now(UTC).isoformat()


def main():
    # Create archive directory with timestamp
    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    archive_path = ARCHIVE_DIR / f"world_{timestamp}"
    archive_path.mkdir(parents=True, exist_ok=True)
    
    print(f"=== World Restart ===")
    print(f"Archiving to: {archive_path}")
    
    # Archive current state
    if STATE_PATH.exists():
        shutil.copy(STATE_PATH, archive_path / "world-state.json")
        print(f"  ✓ Archived world-state.json")
    else:
        print(f"  ! No world-state.json found")
    
    # Archive turn logs
    if TURN_LOG_DIR.exists():
        dest_logs = archive_path / "turn-log"
        dest_logs.mkdir(parents=True, exist_ok=True)
        for log_file in TURN_LOG_DIR.glob("turn-*.json"):
            shutil.copy(log_file, dest_logs / log_file.name)
            print(f"  ✓ Archived {log_file.name}")
    else:
        print(f"  ! No turn-log directory found")
    
    # Create fresh world state at turn 1
    fresh_state = {
        "turn": 1,
        "status": "ready",
        "turnOrder": ["nation_1", "nation_2", "nation_3"],
        "nations": [
            {
                "id": "nation_1",
                "name": "Republic of Hodges",
                "treasury": 6,
                "force": 4,
                "food": 6,
                "stability": 7,
                "industry": 6,
                "relationships": {
                    "nation_2": 1,
                    "nation_3": 0
                }
            },
            {
                "id": "nation_2",
                "name": "Aksumite League",
                "treasury": 7,
                "force": 5,
                "food": 5,
                "stability": 6,
                "industry": 6,
                "relationships": {
                    "nation_1": 1,
                    "nation_3": 0
                }
            },
            {
                "id": "nation_3",
                "name": "Kingdom of Urartu",
                "treasury": 5,
                "force": 7,
                "food": 6,
                "stability": 7,
                "industry": 5,
                "relationships": {
                    "nation_1": 0,
                    "nation_2": 0
                }
            }
        ],
        "treaties": [],
        "wars": [],
        "publicEvents": [
            "The world enters its first monitored turn under judge supervision."
        ],
        "updatedAt": now_iso()
    }
    
    # Clear turn log directory
    if TURN_LOG_DIR.exists():
        for log_file in TURN_LOG_DIR.glob("turn-*.json"):
            log_file.unlink()
        print(f"  ✓ Cleared turn logs")
    
    # Write fresh state
    STATE_PATH.write_text(json.dumps(fresh_state, indent=2) + "\n")
    print(f"  ✓ Reset to turn 1")
    
    print(f"\n=== World reset complete ===")
    print(f"Archived to: {archive_path}")
    print(f"Starting fresh from Turn 1")


if __name__ == "__main__":
    main()