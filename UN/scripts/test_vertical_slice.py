#!/usr/bin/env python3
import json
from copy import deepcopy
from datetime import datetime, UTC
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE_PATH = ROOT / "world" / "world-state.json"
TURN_LOG_DIR = ROOT / "world" / "turn-log"


def clamp(value, low=-5, high=5):
    return max(low, min(high, value))


def load_state():
    return json.loads(STATE_PATH.read_text())


def save_state(state):
    state["updatedAt"] = datetime.now(UTC).isoformat()
    STATE_PATH.write_text(json.dumps(state, indent=2) + "\n")


def nations_by_id(state):
    return {n["id"]: n for n in state["nations"]}


def stat_delta(deltas, nation_id, key, amount):
    if amount == 0:
        return
    deltas.setdefault(nation_id, {}).setdefault("stats", {}).setdefault(key, 0)
    deltas[nation_id]["stats"][key] += amount


def rel_delta(deltas, a, b, amount):
    if amount == 0:
        return
    key = f"{a}->{b}"
    deltas.setdefault("relationships", {}).setdefault(key, 0)
    deltas["relationships"][key] += amount


def apply_action(state, package, action, deltas, notes):
    nation = nations_by_id(state)[package["nation"]]
    action_type = action["type"]
    target = action["target"]
    intensity = action["intensity"]
    summary = action["summary"]

    scale = {"low": 0, "medium": 1, "high": 1}[intensity]

    if action_type == "economy":
        stat_delta(deltas, nation["id"], "treasury", 1)
        if intensity != "low":
            stat_delta(deltas, nation["id"], "industry", scale)
        notes.append(f"{nation['name']} improved its fiscal position through: {summary}")

    elif action_type == "infrastructure":
        stat_delta(deltas, nation["id"], "industry", 1)
        stat_delta(deltas, nation["id"], "food", 1 if "irrig" in summary.lower() else 0)
        notes.append(f"{nation['name']} strengthened its domestic base through: {summary}")

    elif action_type == "internal":
        stat_delta(deltas, nation["id"], "stability", 1)
        if intensity == "high":
            stat_delta(deltas, nation["id"], "treasury", -1)
        notes.append(f"{nation['name']} focused inward: {summary}")

    elif action_type == "diplomacy":
        if target != "none":
            rel = nation["relationships"].get(target, 0)
            change = 1 if rel >= -1 else 0
            rel_delta(deltas, nation["id"], target, change)
            notes.append(f"{nation['name']} pursued diplomacy toward {target}: {summary}")

    elif action_type == "military":
        stat_delta(deltas, nation["id"], "force", 1)
        if intensity != "low":
            stat_delta(deltas, nation["id"], "treasury", -1)
        if target != "none":
            rel_delta(deltas, nation["id"], target, -1)
        notes.append(f"{nation['name']} signaled force via: {summary}")


def apply_deltas(state, deltas):
    by_id = nations_by_id(state)
    for nation_id, payload in deltas.items():
        if nation_id == "relationships":
            continue
        nation = by_id[nation_id]
        for key, amount in payload.get("stats", {}).items():
            nation[key] = max(0, min(10, nation[key] + amount))

    for edge, amount in deltas.get("relationships", {}).items():
        a, b = edge.split("->")
        by_id[a]["relationships"][b] = clamp(by_id[a]["relationships"].get(b, 0) + amount)
        by_id[b]["relationships"][a] = clamp(by_id[b]["relationships"].get(a, 0) + amount)


def summarize_turn(turn, packages, deltas):
    lines = [f"Turn {turn}: all three nations acted under the v0.1 ruleset."]
    for package in packages:
        lines.append(f"- {package['nation']} chose {package['actions'][0]['type']} + {package['actions'][1]['type']} ({package['risk']} risk).")
    if deltas.get("relationships"):
        lines.append("- Diplomacy and pressure shifted several bilateral relationships.")
    return lines


def scripted_packages(turn):
    script = {
        1: [
            {
                "turn": 1,
                "nation": "nation_1",
                "risk": "medium",
                "public_message": "Hodges prefers open trade and stable borders.",
                "actions": [
                    {"type": "diplomacy", "target": "nation_2", "summary": "Offer a limited trade and non-aggression framework.", "intensity": "medium"},
                    {"type": "infrastructure", "target": "none", "summary": "Expand port and customs capacity.", "intensity": "medium"}
                ]
            },
            {
                "turn": 1,
                "nation": "nation_2",
                "risk": "medium",
                "public_message": "The League seeks profitable routes under respected terms.",
                "actions": [
                    {"type": "economy", "target": "none", "summary": "Fund caravan and harbor commerce networks.", "intensity": "medium"},
                    {"type": "diplomacy", "target": "nation_1", "summary": "Respond favorably to a limited trade accord with Hodges.", "intensity": "medium"}
                ]
            },
            {
                "turn": 1,
                "nation": "nation_3",
                "risk": "low",
                "public_message": "Urartu invests first in strength that endures.",
                "actions": [
                    {"type": "infrastructure", "target": "none", "summary": "Reinforce frontier roads and supply depots.", "intensity": "medium"},
                    {"type": "internal", "target": "none", "summary": "Tighten provincial command discipline.", "intensity": "low"}
                ]
            }
        ],
        2: [
            {
                "turn": 2,
                "nation": "nation_1",
                "risk": "medium",
                "public_message": "Hodges will protect commerce without surrendering order.",
                "actions": [
                    {"type": "economy", "target": "none", "summary": "Expand regulated merchant finance.", "intensity": "medium"},
                    {"type": "diplomacy", "target": "nation_3", "summary": "Propose a border transparency understanding with Urartu.", "intensity": "low"}
                ]
            },
            {
                "turn": 2,
                "nation": "nation_2",
                "risk": "high",
                "public_message": "Trade routes will remain open to those who respect them.",
                "actions": [
                    {"type": "military", "target": "nation_3", "summary": "Conduct a forceful trade-route patrol near contested approaches.", "intensity": "medium"},
                    {"type": "economy", "target": "none", "summary": "Leverage rising trade revenues into state reserves.", "intensity": "medium"}
                ]
            },
            {
                "turn": 2,
                "nation": "nation_3",
                "risk": "medium",
                "public_message": "Urartu answers pressure with preparation, not panic.",
                "actions": [
                    {"type": "military", "target": "nation_2", "summary": "Reinforce mountain border garrisons facing the League.", "intensity": "medium"},
                    {"type": "internal", "target": "none", "summary": "Stabilize frontier command and ration stores.", "intensity": "medium"}
                ]
            }
        ],
        3: [
            {
                "turn": 3,
                "nation": "nation_1",
                "risk": "medium",
                "public_message": "Hodges calls for de-escalation and enforceable terms.",
                "actions": [
                    {"type": "diplomacy", "target": "nation_2", "summary": "Urge restraint and propose monitored trade guarantees.", "intensity": "medium"},
                    {"type": "internal", "target": "none", "summary": "Fund civic confidence and emergency reserves.", "intensity": "medium"}
                ]
            },
            {
                "turn": 3,
                "nation": "nation_2",
                "risk": "medium",
                "public_message": "Prestige is best secured by profitable calm, not wasteful fury.",
                "actions": [
                    {"type": "diplomacy", "target": "nation_3", "summary": "Offer talks to reduce frontier friction while preserving route access.", "intensity": "medium"},
                    {"type": "infrastructure", "target": "none", "summary": "Improve warehouses and maritime loading capacity.", "intensity": "medium"}
                ]
            },
            {
                "turn": 3,
                "nation": "nation_3",
                "risk": "low",
                "public_message": "Urartu accepts calm backed by stone and grain.",
                "actions": [
                    {"type": "infrastructure", "target": "none", "summary": "Extend irrigation and fortress supply works.", "intensity": "medium"},
                    {"type": "diplomacy", "target": "nation_2", "summary": "Accept limited talks if border pressure is reduced.", "intensity": "low"}
                ]
            }
        ]
    }
    return script[turn]


def main():
    state = load_state()
    snapshots = []

    for turn in [1, 2, 3]:
        state["turn"] = turn
        packages = scripted_packages(turn)
        deltas = {}
        notes = []
        before = deepcopy(state)

        for package in packages:
            for action in package["actions"]:
                apply_action(state, package, action, deltas, notes)

        apply_deltas(state, deltas)
        summary = summarize_turn(turn, packages, deltas)
        state.setdefault("publicEvents", []).extend(summary)
        state["status"] = "running"

        log = {
            "turn": turn,
            "packages": packages,
            "notes": notes,
            "deltas": deltas,
            "summary": summary,
            "before": before,
            "after": deepcopy(state)
        }
        (TURN_LOG_DIR / f"turn-{turn:03d}.json").write_text(json.dumps(log, indent=2) + "\n")
        snapshots.append({"turn": turn, "summary": summary})

    save_state(state)

    print("Vertical slice test completed.")
    for snap in snapshots:
        print(f"\nTurn {snap['turn']}")
        for line in snap["summary"]:
            print(line)


if __name__ == "__main__":
    main()
