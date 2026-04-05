#!/usr/bin/env python3
"""Run World Sim turn - territory actions enabled."""

import json
import math
import random
import subprocess
import time
from copy import deepcopy
from datetime import datetime, UTC
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE_PATH = ROOT / "world" / "world-state.json"
TURN_LOG_DIR = ROOT / "world" / "turn-log"
RULES_DIR = ROOT / "rules"

SUMMIT_CHANNEL = "channel:1482491159367389314"
WORLD_NEWS_CHANNEL = "channel:1482491117734985808"

ACCOUNT_BY_NATION = {"nation_1": "nation1bot", "nation_2": "nation2bot", "nation_3": "nation3bot"}
JUDGE_ACCOUNT = "judgebot"

DEBUG = False  # False=readable, True=JSON in summit

UNIT_STATS = {
    "militia": {"cost": 1, "attack": 1, "defense": 1},
    "soldier": {"cost": 2, "attack": 2, "defense": 2},
    "legion": {"cost": 3, "attack": 4, "defense": 3},
    "cavalry": {"cost": 3, "attack": 3, "defense": 2},
    "siege": {"cost": 4, "attack": 5, "defense": 1},
}


def now_iso():
    return datetime.now(UTC).isoformat()


def sh(cmd, timeout_s=180):
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_s)
    if proc.returncode != 0:
        raise RuntimeError(f"Cmd failed: {' '.join(cmd)}\n{proc.stderr}")
    return proc.stdout


def msg_read(ch, target, limit=50, after=None):
    cmd = ["openclaw", "message", "read", "--channel", ch, "--target", target, "--limit", str(limit), "--json"]
    if after: cmd += ["--after", after]
    return json.loads(sh(cmd))


def msg_send(ch, target, message, account=None):
    cmd = ["openclaw", "message", "send", "--channel", ch, "--target", target, "--message", message]
    if account: cmd += ["--account", account]
    cmd += ["--json"]
    sh(cmd)


def agent_deliver(agent_id, message, reply_ch, reply_to, reply_account, timeout_s=600):
    cmd = ["openclaw", "agent", "--agent", agent_id, "--message", message, "--deliver",
           "--reply-channel", reply_ch, "--reply-to", reply_to, "--reply-account", reply_account,
           "--json", "--timeout", str(timeout_s)]
    return json.loads(sh(cmd, timeout_s + 30))


def extract_json(text, turn, nation_id):
    import re
    text = text.strip()
    
    # Try multiple extraction strategies
    for block in re.findall(r"```json\s*([\s\S]*?)```", text):
        try:
            p = json.loads(block.strip())
            if p.get("turn") == turn and p.get("nation") == nation_id:
                if "actions" in p and isinstance(p["actions"], list):
                    return p
        except:
            pass
    
    # Try raw JSON object anywhere
    for m in re.finditer(r"\{", text):
        for end in range(m.end(), len(text)):
            if text[end] == "}":
                try:
                    p = json.loads(text[m.start():end+1])
                    if p.get("turn") == turn and p.get("nation") == nation_id:
                        if "actions" in p:
                            return p
                except:
                    pass
    
    # Lenient: return basic package if turn matches
    if str(turn) in text and "nation" in text:
        return {"turn": turn, "nation": nation_id, "risk": "medium", 
                "actions": [{"type": "economy", "target": "none", "summary": "default", "intensity": "medium"}]}
    
    raise ValueError("No valid package")


def load_state():
    return json.loads(STATE_PATH.read_text())


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n")


def get_public_state(state):
    """Extract public-facing state."""
    nation_names = {
        "nation_1": "Republic of Hodges",
        "nation_2": "Aksumite League", 
        "nation_3": "Kingdom of Urartu"
    }
    return {
        "turn": state["turn"],
        "turnOrder": state["turnOrder"],
        "nations": [{
            "id": n["id"],
            "name": nation_names.get(n["id"], n["id"]),
            "treasury": n.get("treasury", 0),
            "force": n.get("force", 0),
            "food": n.get("food", 0),
            "stability": n.get("stability", 0),
            "industry": n.get("industry", 0),
            "relationships": n.get("relationships", {})
        } for n in state.get("nations", [])],
        "cityOwnership": state.get("cityOwnership", {}),
        "cities": state.get("cities", {}),
        "treaties": state.get("treaties", []),
    }


def build_nation_prompt(turn, nation_id, state, summit_msgs, debug=False):
    schema = (RULES_DIR / "action-schema.md").read_text()
    public = get_public_state(state)
    state_json = json.dumps(public, indent=2)
    nation_names = {"nation_1": "Hodges", "nation_2": "Aksum", "nation_3": "Urartu"}
    
    debug_note = "\n\n## DEBUG MODE: ON\nInclude your full JSON in the message as ```json block```" if debug else ""
    
    return (
        f"Turn: {turn}\nNation id: {nation_id}\n"
        f"Your agenda: {state['nations'][int(nation_id.split('_')[1])-1]['agenda']['name']}\n\n"
        f"## Your Task\n"
        f"Post ONE message in #summit with:\n"
        f"1. Public statement (readable, 1-3 lines) - address @{nation_names.get(nation_id, nation_id)} if targeting\n"
        f"2. Two actions you take this turn\n\n"
        "## Available Actions\n"
        "### TERRITORY (v0.2)\n"
        "- army: {'type':'army','source':'city_X','target':'city_Y','unit':'soldier','count':1,'mission':'conquer'}\n"
        "- buy: {'type':'buy','target':'city_X'}  (buy neutral city)\n"
        "- fortify: {'type':'fortify','target':'city_X'}  (+defense)\n\n"
        "### LEGACY\n"
        "- economy, infrastructure, internal, diplomacy, military (v0.1 format)\n\n"
        f"## Current State\n{state_json}{debug_note}"
    )


# === TERRITORY ACTIONS LOGIC ===

def resolve_army_action(state, action, nation_id, notes):
    """Handle army movement/conquest."""
    source = action.get("source")
    target = action.get("target")
    unit_type = action.get("unit", "soldier")
    count = action.get("count", 1)
    mission = action.get("mission", "conquer")
    
    cities = state.get("cities", {})
    owner_map = state.get("cityOwnership", {})
    
    # Validate
    if source not in cities or target not in cities:
        notes.append(f"{nation_id}: invalid city in army action")
        return state
    
    if owner_map.get(source) != nation_id:
        notes.append(f"{nation_id}: doesn't own {source}")
        return state
    
    # Check connection
    connections = state.get("connections", [])
    connected = any(source in c and target in c for c in connections)
    if not connected:
        notes.append(f"{nation_id}: {source} not connected to {target}")
        return state
    
    # Check population cost
    stats = UNIT_STATS.get(unit_type, UNIT_STATS["soldier"])
    cost = stats["cost"] * count
    
    source_city = cities[source]
    if source_city.get("population", 0) < cost:
        notes.append(f"{nation_id}: not enough pop in {source}")
        return state
    
    # Deduct population
    source_city["population"] = max(0, source_city["population"] - cost)
    notes.append(f"{nation_id}: {count}x {unit_type} moved from {source}")
    
    # Check target owner
    target_owner = owner_map.get(target)
    
    if target_owner is None:
        # Neutral - auto capture
        owner_map[target] = nation_id
        cities[target]["owner"] = nation_id
        cities[target]["population"] = max(1, cities[target]["population"])
        cities[target]["units"] = [{"type": unit_type, "count": count}]
        notes.append(f"{nation_id}: captured {target}")
    elif target_owner == nation_id:
        # Own city - reinforce
        city = cities[target]
        city.setdefault("units", [])
        city["units"].append({"type": unit_type, "count": count})
        notes.append(f"{nation_id}: reinforced {target}")
    else:
        # Battle!
        attacker_power = (stats["attack"] * count) + math.sqrt(source_city.get("population", 1))
        
        defender_city = cities[target]
        defender_stats = UNIT_STATS.get("soldier", {"cost": 2, "attack": 2, "defense": 2})
        defender_units = defender_city.get("units", [])
        defense_units_power = sum(UNIT_STATS.get(u["type"], UNIT_STATS["soldier"])["defense"] * u.get("count", 1) for u in defender_units)
        defender_power = (defender_city.get("fortification", 1) + math.sqrt(defender_city.get("population", 1)) + 2)  # +2 home bonus
        
        if attacker_power > defender_power:
            # Win
            owner_map[target] = nation_id
            defender_city["owner"] = nation_id
            defender_city["population"] = max(1, defender_city["population"] // 2)
            defender_city["units"] = [{"type": unit_type, "count": count}]
            cities[source]["units"] = [{"type": unit_type, "count": cost // stats["cost"]}]  # Remaining
            notes.append(f"{nation_id}: won battle for {target}")
        else:
            # Lose - retreat with losses
            loss = cost // 2
            source_city["population"] = max(0, source_city.get("population", 0) - cost) + loss
            notes.append(f"{nation_id}: lost battle for {target}, retreated")
    
    return state


def resolve_buy_action(state, action, nation_id, notes):
    """Handle buying neutral cities."""
    target = action.get("target")
    cities = state.get("cities", {})
    owner_map = state.get("cityOwnership", {})
    
    if target not in cities:
        notes.append(f"{nation_id}: invalid city {target}")
        return state
    
    if owner_map.get(target) is not None:
        notes.append(f"{nation_id}: {target} already owned")
        return state
    
    # Calculate cost
    nation = next((n for n in state["nations"] if n["id"] == nation_id), None)
    if not nation:
        return state
    
    industry = nation.get("industry", 0)
    cost = max(1, 2 - (industry // 2))
    
    treasury = nation.get("treasury", 0)
    if treasury < cost:
        notes.append(f"{nation_id}: not enough treasury ({treasury} < {cost})")
        return state
    
    # Deduct and buy
    nation["treasury"] -= cost
    owner_map[target] = nation_id
    cities[target]["owner"] = nation_id
    notes.append(f"{nation_id}: bought {target} for {cost}")
    
    return state


def resolve_fortify_action(state, action, nation_id, notes):
    """Increase city fortification."""
    target = action.get("target")
    cities = state.get("cities", {})
    owner_map = state.get("cityOwnership", {})
    
    if target not in cities:
        return state
    if owner_map.get(target) != nation_id:
        notes.append(f"{nation_id}: doesn't own {target}")
        return state
    
    city = cities[target]
    city["fortification"] = min(10, city.get("fortification", 0) + 1)
    notes.append(f"{nation_id}: +1 fort on {target}")
    
    return state


def resolve_legacy_action(state, action, nation_id, notes):
    """Handle v0.1 actions."""
    action_type = action.get("type")
    intensity = action.get("intensity", "medium")
    scale = {"low": 0, "medium": 1, "high": 1}.get(intensity, 0)
    
    by_id = {n["id"]: n for n in state["nations"]}
    nation = by_id.get(nation_id)
    if not nation:
        return state
    
    if action_type == "economy":
        nation["treasury"] = min(10, nation["treasury"] + 1)
        if intensity != "low":
            nation["industry"] = min(10, nation["industry"] + scale)
        notes.append(f"{nation_id}: economy +1")
    elif action_type == "infrastructure":
        nation["industry"] = min(10, nation["industry"] + 1)
        notes.append(f"{nation_id}: infrastructure +1")
    elif action_type == "internal":
        nation["stability"] = min(10, nation["stability"] + 1)
        notes.append(f"{nation_id}: internal +1")
    elif action_type == "diplomacy":
        target = action.get("target", "none")
        if target != "none" and target in nation.get("relationships", {}):
            nation["relationships"][target] = min(5, nation["relationships"][target] + 1)
            if target in by_id:
                by_id[target]["relationships"][nation_id] = min(5, by_id[target]["relationships"].get(nation_id, 0) + 1)
            notes.append(f"{nation_id}: diplomacy +1 with {target}")
    elif action_type == "military":
        nation["force"] = min(10, nation["force"] + 1)
        if intensity != "low":
            nation["treasury"] = max(0, nation["treasury"] - 1)
        target = action.get("target", "none")
        if target != "none" and target in nation.get("relationships", {}):
            nation["relationships"][target] = max(-5, nation["relationships"][target] - 1)
            notes.append(f"{nation_id}: military pressure on {target}")
    
    return state


def apply_actions(state, actions, nation_id, notes):
    """Apply all actions for a nation."""
    for action in actions:
        action_type = action.get("type")
        
        if action_type == "army":
            state = resolve_army_action(state, action, nation_id, notes)
        elif action_type == "buy":
            state = resolve_buy_action(state, action, nation_id, notes)
        elif action_type == "fortify":
            state = resolve_fortify_action(state, action, nation_id, notes)
        else:
            state = resolve_legacy_action(state, action, nation_id, notes)
    
    return state


def main():
    state = load_state()
    before = deepcopy(state)
    turn = state["turn"] + 1
    
    print(f"\n=== Turn {turn} ===")
    
    # Announce
    msg_send("discord", WORLD_NEWS_CHANNEL, f"⚖️ **[TURN {turn} START]**", account=JUDGE_ACCOUNT)
    
    # Get baseline
    data = msg_read("discord", SUMMIT_CHANNEL, limit=1)
    after_id = data.get("payload", {}).get("messages", [{}])[0].get("id")
    
    summit_history = []
    packages = {}
    
    # Each nation
    for nation_id in state["turnOrder"]:
        print(f"  Processing {nation_id}...")
        prompt = build_nation_prompt(turn, nation_id, state, summit_history)
        
        run = agent_deliver(nation_id, prompt, "discord", SUMMIT_CHANNEL, ACCOUNT_BY_NATION[nation_id], 600)
        reply = "\n".join(p.get("text", "") for p in run.get("result", {}).get("payloads", []))
        
        # Get their summit post
        time.sleep(3)
        data = msg_read("discord", SUMMIT_CHANNEL, limit=20, after=after_id)
        new_msgs = data.get("payload", {}).get("messages", [])
        if new_msgs:
            after_id = new_msgs[0]["id"]
            summit_history.extend(new_msgs)
        
        pkg = extract_json(reply, turn, nation_id)
        packages[nation_id] = pkg
        print(f"    ✓ Got package")
    
    # Apply all actions
    all_notes = []
    for nation_id, pkg in packages.items():
        notes = []
        state = apply_actions(state, pkg.get("actions", []), nation_id, notes)
        all_notes.extend(notes)
        print(f"  {nation_id}: {len(notes)} effects")
    
    state["turn"] = turn
    state["status"] = "running"
    state["updatedAt"] = now_iso()
    
    # Persist
    write_json(STATE_PATH, state)
    log = {"turn": turn, "notes": all_notes, "before": before, "after": deepcopy(state)}
    write_json(TURN_LOG_DIR / f"turn-{turn:03d}.json", log)
    
    # Post summary
    lines = [f"⚖️ **Turn {turn} Complete**"]
    lines.append(f"**Actions:** {len(all_notes)}")
    for n in state["nations"]:
        lines.append(f"  {n['id']}: T{n['treasury']} F{n['force']} Food{n['food']} S{n['stability']} I{n['industry']}")
    msg_send("discord", SUMMIT_CHANNEL, "\n".join(lines), account=JUDGE_ACCOUNT)
    
    print(f"\n=== Turn {turn} done ===")
    if DEBUG:
        print(json.dumps(state, indent=2)[:600] + "...")


if __name__ == "__main__":
    main()