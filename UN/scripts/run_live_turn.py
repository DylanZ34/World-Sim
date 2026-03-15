#!/usr/bin/env python3
import json
from copy import deepcopy
from datetime import datetime, UTC
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
STATE_PATH = ROOT / "world" / "world-state.json"
TURN_LOG_DIR = ROOT / "world" / "turn-log"

NATION_CONFIG = {
    "nation_1": {
        "name": "Republic of Hodges",
        "workspace": REPO / "nations" / "nation_1",
        "style": "republic"
    },
    "nation_2": {
        "name": "Aksumite League",
        "workspace": REPO / "nations" / "nation_2",
        "style": "trade_empire"
    },
    "nation_3": {
        "name": "Kingdom of Urartu",
        "workspace": REPO / "nations" / "nation_3",
        "style": "fortress"
    }
}


def now_iso():
    return datetime.now(UTC).isoformat()


def clamp(value, low, high):
    return max(low, min(high, value))


def load_json(path: Path):
    return json.loads(path.read_text())


def write_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n")


def nation_map(state):
    return {nation["id"]: nation for nation in state["nations"]}


def weakest_relationship(nation):
    pairs = list(nation["relationships"].items())
    pairs.sort(key=lambda item: item[1])
    return pairs[0]


def strongest_relationship(nation):
    pairs = list(nation["relationships"].items())
    pairs.sort(key=lambda item: item[1], reverse=True)
    return pairs[0]


def make_package(turn, nation_id, state):
    nation = nation_map(state)[nation_id]
    style = NATION_CONFIG[nation_id]["style"]
    weakest_target, weakest_score = weakest_relationship(nation)
    strongest_target, strongest_score = strongest_relationship(nation)

    if style == "republic":
        if weakest_score <= -2:
            return {
                "turn": turn,
                "nation": nation_id,
                "risk": "medium",
                "public_message": "Hodges seeks enforceable calm, stable trade, and defensible order.",
                "actions": [
                    {
                        "type": "diplomacy",
                        "target": weakest_target,
                        "summary": f"Propose monitored de-escalation terms and border transparency with {weakest_target}.",
                        "intensity": "medium"
                    },
                    {
                        "type": "internal",
                        "target": "none",
                        "summary": "Fund public confidence, legal coordination, and emergency reserves.",
                        "intensity": "medium"
                    }
                ]
            }
        return {
            "turn": turn,
            "nation": nation_id,
            "risk": "medium",
            "public_message": "Hodges favors lawful prosperity and stable relations among sovereign states.",
            "actions": [
                {
                    "type": "diplomacy",
                    "target": strongest_target,
                    "summary": f"Pursue a rules-based trade and non-aggression framework with {strongest_target}.",
                    "intensity": "medium"
                },
                {
                    "type": "infrastructure",
                    "target": "none",
                    "summary": "Expand port capacity, customs administration, and commercial logistics.",
                    "intensity": "medium"
                }
            ]
        }

    if style == "trade_empire":
        if weakest_score <= -2:
            return {
                "turn": turn,
                "nation": nation_id,
                "risk": "medium",
                "public_message": "The League prefers profitable passage, but it will not neglect strategic leverage.",
                "actions": [
                    {
                        "type": "diplomacy",
                        "target": weakest_target,
                        "summary": f"Offer structured talks on reducing friction with {weakest_target} while preserving route access.",
                        "intensity": "medium"
                    },
                    {
                        "type": "economy",
                        "target": "none",
                        "summary": "Increase treasury reserves through coordinated trade and port revenues.",
                        "intensity": "medium"
                    }
                ]
            }
        return {
            "turn": turn,
            "nation": nation_id,
            "risk": "medium",
            "public_message": "The League extends commerce where respect and access are properly maintained.",
            "actions": [
                {
                    "type": "economy",
                    "target": "none",
                    "summary": "Invest in caravan, harbor, and customs networks to expand trade throughput.",
                    "intensity": "medium"
                },
                {
                    "type": "diplomacy",
                    "target": strongest_target,
                    "summary": f"Seek a favorable trade understanding with {strongest_target}.",
                    "intensity": "medium"
                }
            ]
        }

    if style == "fortress":
        if weakest_score <= -1:
            return {
                "turn": turn,
                "nation": nation_id,
                "risk": "medium",
                "public_message": "Urartu answers uncertainty with readiness and durable stores.",
                "actions": [
                    {
                        "type": "military",
                        "target": weakest_target,
                        "summary": f"Reinforce frontier garrisons and defensive patrols facing {weakest_target}.",
                        "intensity": "medium"
                    },
                    {
                        "type": "infrastructure",
                        "target": "none",
                        "summary": "Expand depots, road links, irrigation, and fortress supply depth.",
                        "intensity": "medium"
                    }
                ]
            }
        return {
            "turn": turn,
            "nation": nation_id,
            "risk": "low",
            "public_message": "Urartu builds strength that does not depend on the moods of others.",
            "actions": [
                {
                    "type": "infrastructure",
                    "target": "none",
                    "summary": "Improve frontier roads, irrigation works, and storehouse resilience.",
                    "intensity": "medium"
                },
                {
                    "type": "internal",
                    "target": "none",
                    "summary": "Tighten provincial discipline and strategic reserve administration.",
                    "intensity": "low"
                }
            ]
        }

    raise ValueError(f"Unknown nation style: {style}")


def add_stat_delta(deltas, nation_id, stat, amount):
    if amount == 0:
        return
    deltas.setdefault("stats", {}).setdefault(nation_id, {}).setdefault(stat, 0)
    deltas["stats"][nation_id][stat] += amount


def add_relationship_delta(deltas, a, b, amount):
    if amount == 0:
        return
    key = tuple(sorted([a, b]))
    deltas.setdefault("relationships", {}).setdefault(key, 0)
    deltas["relationships"][key] += amount


def action_effect(state, package, action, deltas, judge_notes):
    nation = nation_map(state)[package["nation"]]
    action_type = action["type"]
    target = action["target"]
    intensity = action["intensity"]
    summary = action["summary"]

    if action_type == "economy":
        add_stat_delta(deltas, nation["id"], "treasury", 1)
        add_stat_delta(deltas, nation["id"], "industry", 1 if intensity != "low" else 0)
        judge_notes.append(f"{nation['name']} expanded economic capacity.")

    elif action_type == "infrastructure":
        add_stat_delta(deltas, nation["id"], "industry", 1)
        if any(word in summary.lower() for word in ["irrig", "store", "supply", "depot"]):
            add_stat_delta(deltas, nation["id"], "food", 1)
        judge_notes.append(f"{nation['name']} deepened internal capacity and resilience.")

    elif action_type == "internal":
        add_stat_delta(deltas, nation["id"], "stability", 1)
        judge_notes.append(f"{nation['name']} improved domestic cohesion.")

    elif action_type == "diplomacy":
        if target != "none":
            add_relationship_delta(deltas, nation["id"], target, 1)
            judge_notes.append(f"{nation['name']} sought improved relations with {target}.")

    elif action_type == "military":
        add_stat_delta(deltas, nation["id"], "force", 1)
        add_stat_delta(deltas, nation["id"], "treasury", -1 if intensity != "low" else 0)
        if target != "none":
            add_relationship_delta(deltas, nation["id"], target, -1)
            judge_notes.append(f"{nation['name']} applied visible military pressure toward {target}.")


def apply_package_synergies(packages, deltas, judge_notes):
    diplomacy_targets = {}
    military_edges = set()

    for package in packages:
        for action in package["actions"]:
            if action["type"] == "diplomacy" and action["target"] != "none":
                diplomacy_targets[(package["nation"], action["target"])] = action
            if action["type"] == "military" and action["target"] != "none":
                military_edges.add((package["nation"], action["target"]))

    for (a, b), _action in diplomacy_targets.items():
        if (b, a) in diplomacy_targets:
            add_relationship_delta(deltas, a, b, 1)
            judge_notes.append(f"Reciprocal diplomacy between {a} and {b} produced extra warming.")

    for edge in list(deltas.get("relationships", {}).keys()):
        a, b = edge
        if (a, b) in military_edges or (b, a) in military_edges:
            if deltas["relationships"][edge] > 0:
                deltas["relationships"][edge] -= 1
                judge_notes.append(f"Military tension partially offset diplomatic gains between {a} and {b}.")


def apply_deltas(state, deltas):
    by_id = nation_map(state)
    for nation_id, stats in deltas.get("stats", {}).items():
        nation = by_id[nation_id]
        for stat, amount in stats.items():
            nation[stat] = clamp(nation[stat] + amount, 0, 10)

    for (a, b), amount in deltas.get("relationships", {}).items():
        by_id[a]["relationships"][b] = clamp(by_id[a]["relationships"][b] + amount, -5, 5)
        by_id[b]["relationships"][a] = clamp(by_id[b]["relationships"][a] + amount, -5, 5)


def build_treaties_and_wars(state):
    treaties = []
    wars = []
    by_id = nation_map(state)
    seen = set()
    for a, nation in by_id.items():
        for b, score in nation["relationships"].items():
            key = tuple(sorted([a, b]))
            if key in seen:
                continue
            seen.add(key)
            if score >= 4:
                treaties.append({"parties": [a, b], "type": "trade-understanding"})
            if score <= -4:
                wars.append({"parties": [a, b], "type": "active-crisis"})
    state["treaties"] = treaties
    state["wars"] = wars


def summarize_turn(turn, packages, deltas, state):
    by_id = nation_map(state)
    lines = [f"Turn {turn} concluded under judge supervision."]
    for package in packages:
        nation = package["nation"]
        action_names = " + ".join(action["type"] for action in package["actions"])
        lines.append(f"- {NATION_CONFIG[nation]['name']} chose {action_names} ({package['risk']} risk).")
    if state["treaties"]:
        lines.append("- Strong alignment hardened into at least one standing understanding.")
    if state["wars"]:
        lines.append("- At least one relationship crossed into open crisis.")
    else:
        tense = []
        for nation in state["nations"]:
            for other, score in nation["relationships"].items():
                if nation["id"] < other and score <= -2:
                    tense.append((nation["id"], other, score))
        if tense:
            lines.append("- Tension remains active in at least one bilateral frontier.")
    lines.append("- Status snapshot: " + ", ".join(
        f"{nation['id']} T{nation['treasury']} F{nation['force']} Food{nation['food']} S{nation['stability']} I{nation['industry']}"
        for nation in by_id.values()
    ))
    return lines


def append_public_events(state, lines):
    state.setdefault("publicEvents", []).extend(lines)
    if len(state["publicEvents"]) > 30:
        state["publicEvents"] = state["publicEvents"][-30:]


def write_nation_outputs(turn, state, packages):
    for package in packages:
        config = NATION_CONFIG[package["nation"]]
        live_dir = config["workspace"] / "state"
        live_dir.mkdir(parents=True, exist_ok=True)
        payload = {
            "generatedAt": now_iso(),
            "turn": turn,
            "nation": package["nation"],
            "package": package,
            "visibleState": nation_map(state)[package["nation"]]
        }
        write_json(live_dir / f"turn-{turn:03d}-submission.json", payload)


def write_judge_log(turn, before, packages, deltas, judge_notes, state, summary):
    payload = {
        "turn": turn,
        "generatedAt": now_iso(),
        "packages": packages,
        "judgeNotes": judge_notes,
        "deltas": {
            "stats": deltas.get("stats", {}),
            "relationships": {f"{a}<->{b}": amount for (a, b), amount in deltas.get("relationships", {}).items()}
        },
        "before": before,
        "after": deepcopy(state),
        "summary": summary
    }
    write_json(TURN_LOG_DIR / f"turn-{turn:03d}.json", payload)


def main():
    state = load_json(STATE_PATH)
    before = deepcopy(state)
    turn = state["turn"] + 1
    state["turn"] = turn
    state["status"] = "running"

    packages = [make_package(turn, nation_id, state) for nation_id in state["turnOrder"]]
    deltas = {}
    judge_notes = []

    for package in packages:
        for action in package["actions"]:
            action_effect(state, package, action, deltas, judge_notes)

    apply_package_synergies(packages, deltas, judge_notes)
    apply_deltas(state, deltas)
    build_treaties_and_wars(state)
    summary = summarize_turn(turn, packages, deltas, state)
    append_public_events(state, summary)
    state["updatedAt"] = now_iso()

    write_nation_outputs(turn, state, packages)
    write_judge_log(turn, before, packages, deltas, judge_notes, state, summary)
    write_json(STATE_PATH, state)

    print(f"Ran live turn {turn}.")
    for line in summary:
        print(line)


if __name__ == "__main__":
    main()
