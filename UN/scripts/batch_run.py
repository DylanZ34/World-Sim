#!/usr/bin/env python3
"""Batch run script for World Sim.

Usage:
    python3 batch_run.py [num_turns] [debug]

Arguments:
    num_turns: Number of turns to run (default: 10)
    debug: Enable debug mode (default: False)

Example:
    python3 batch_run.py 5 True    # Run 5 turns with debug
    python3 batch_run.py           # Run 10 turns, no debug
"""

import json
import subprocess
import time
import sys
from copy import deepcopy
from datetime import datetime, UTC
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE_PATH = ROOT / "world" / "world-state.json"
TURN_LOG_DIR = ROOT / "world" / "turn-log"
RULES_DIR = ROOT / "rules"

SUMMIT_CHANNEL = "channel:1482491159367389314"
WORLD_NEWS_CHANNEL = "channel:1482491117734985808"

ACCOUNT_BY_NATION = {
    "nation_1": "nation1bot",
    "nation_2": "nation2bot",
    "nation_3": "nation3bot",
}
JUDGE_ACCOUNT = "judgebot"


def parse_args():
    """Parse command line arguments."""
    num_turns = 10
    debug = False
    
    if len(sys.argv) > 1:
        try:
            num_turns = int(sys.argv[1])
        except ValueError:
            print(f"Invalid num_turns: {sys.argv[1]}, using default 10")
    
    if len(sys.argv) > 2:
        debug = sys.argv[2].lower() in ("true", "1", "yes", "on")
    
    return num_turns, debug


def now_iso():
    return datetime.now(UTC).isoformat()


def sh(cmd: list[str], timeout_s: int = 180):
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_s)
    if proc.returncode != 0:
        raise RuntimeError(f"Command failed ({proc.returncode}): {' '.join(cmd)}\nSTDERR:\n{proc.stderr}")
    return proc.stdout


def openclaw_message_read(channel: str, target: str, limit: int = 50, after: str | None = None):
    cmd = ["openclaw", "message", "read", "--channel", channel, "--target", target, "--limit", str(limit), "--json"]
    if after:
        cmd += ["--after", after]
    out = sh(cmd, timeout_s=180)
    return json.loads(out)


def openclaw_message_send(channel: str, target: str, message: str, account: str | None = None):
    cmd = ["openclaw", "message", "send", "--channel", channel, "--target", target, "--message", message]
    if account:
        cmd += ["--account", account]
    cmd += ["--json"]
    out = sh(cmd, timeout_s=180)
    return json.loads(out)


def openclaw_agent(agent_id: str, message: str, timeout_s: int = 600):
    cmd = [
        "openclaw", "agent", "--agent", agent_id,
        "--message", message,
        "--json", "--timeout", str(timeout_s),
    ]
    out = sh(cmd, timeout_s=timeout_s + 30)
    return json.loads(out)


def load_text(path: Path) -> str:
    return path.read_text()


def load_state():
    return json.loads(STATE_PATH.read_text())


def write_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n")


def get_public_state(state: dict) -> dict:
    return {
        "turn": state["turn"],
        "turnOrder": state["turnOrder"],
        "nations": [
            {
                "id": n["id"],
                "name": n["name"],
                "treasury": n["treasury"],
                "force": n["force"],
                "food": n["food"],
                "stability": n["stability"],
                "industry": n["industry"],
                "relationships": n["relationships"]
            }
            for n in state["nations"]
        ],
        "treaties": state.get("treaties", []),
        "wars": state.get("wars", []),
        "publicEvents": state.get("publicEvents", [])[-5:]
    }


def apply_package(state: dict, package: dict) -> dict:
    nation_id = package["nation"]
    actions = package.get("actions", [])
    
    by_id = {n["id"]: n for n in state["nations"]}
    nation = by_id.get(nation_id)
    if not nation:
        return state
    
    for action in actions:
        action_type = action.get("type", "")
        target = action.get("target", "none")
        intensity = action.get("intensity", "medium")
        summary = action.get("summary", "")
        
        scale = {"low": 0, "medium": 1, "high": 1}.get(intensity, 0)
        
        if action_type == "economy":
            nation["treasury"] = min(10, nation["treasury"] + 1)
            if intensity != "low":
                nation["industry"] = min(10, nation["industry"] + scale)
            
        elif action_type == "infrastructure":
            nation["industry"] = min(10, nation["industry"] + 1)
            if any(w in summary.lower() for w in ["irrig", "food", "grain", "farm"]):
                nation["food"] = min(10, nation["food"] + 1)
            
        elif action_type == "internal":
            nation["stability"] = min(10, nation["stability"] + 1)
            
        elif action_type == "diplomacy":
            if target != "none" and target in nation["relationships"]:
                old = nation["relationships"][target]
                nation["relationships"][target] = min(5, old + 1)
                if target in by_id:
                    other = by_id[target]
                    if nation_id in other["relationships"]:
                        other["relationships"][nation_id] = min(5, other["relationships"][nation_id] + 1)
            
        elif action_type == "military":
            nation["force"] = min(10, nation["force"] + 1)
            if intensity != "low":
                nation["treasury"] = max(0, nation["treasury"] - 1)
            if target != "none" and target in nation["relationships"]:
                old = nation["relationships"][target]
                nation["relationships"][target] = max(-5, old - 1)
                if target in by_id:
                    other = by_id[target]
                    if nation_id in other["relationships"]:
                        other["relationships"][nation_id] = max(-5, other["relationships"][nation_id] - 1)
    
    treaties = []
    wars = []
    for a, na in by_id.items():
        for b, score in na["relationships"].items():
            if a < b:
                if score >= 4:
                    treaties.append({"parties": [a, b], "type": "alignment"})
                elif score <= -4:
                    wars.append({"parties": [a, b], "type": "crisis"})
    
    state["treaties"] = treaties
    state["wars"] = wars
    
    return state


def build_nation_prompt(turn: int, nation_id: str, state: dict, summit_msgs: list[dict]) -> str:
    schema = load_text(RULES_DIR / "action-schema.md")
    nation_prompt_md = load_text(ROOT / "prompts" / "nation-turn-prompt.md")
    public_state = get_public_state(state)
    state_json = json.dumps(public_state, indent=2)
    
    USER_TO_NATION = {"Hodge": "nation_1", "Aksum": "nation_2", "Urartu": "nation_3"}
    nation_name = next(n["name"] for n in public_state["nations"] if n["id"] == nation_id)
    
    mentions = []
    for m in summit_msgs:
        author = m.get("author", {}).get("username")
        author_nation = USER_TO_NATION.get(author)
        content = m.get("content", "")
        if author_nation != nation_id and (f"@{nation_name}" in content or f"@{nation_id}" in content):
            mentions.append(f"- {author}: {content[:150]}...")
    
    mentions_text = ""
    if mentions:
        mentions_text = "\n## Recent messages addressed to you in #summit:\n" + "\n".join(mentions)
    
    return (
        f"{nation_prompt_md}\n\n"
        f"Turn: {turn}\nNation id: {nation_id}\n\n"
        "## Your task - produce a JSON turn package\n"
        "Output ONLY JSON - no markdown, no explanation.\n\n"
        "Format:\n```json\n{\n  \"turn\": " + str(turn) + ",\n  \"nation\": \"" + nation_id + "\",\n  \"risk\": \"medium\",\n  \"public_message\": \"your public statement\",\n  \"actions\": [\n    {\"type\": \"...\", \"target\": \"...\", \"summary\": \"...\", \"intensity\": \"...\"},\n    {\"type\": \"...\", \"target\": \"...\", \"summary\": \"...\", \"intensity\": \"...\"}\n  ]\n}\n```\n\n"
        f"Schema:\n{schema}\n\n"
        f"## Current public state:\n{state_json}\n"
        f"{mentions_text}\n\n"
        "If any action targets another nation, your public_message should start with @Name to address them."
    )


def extract_json(text: str):
    import re
    
    text = text.strip()
    
    blocks = re.findall(r"```json\s*([\s\S]*?)```", text)
    for block in blocks:
        try:
            return json.loads(block.strip())
        except:
            pass
    
    try:
        return json.loads(text)
    except:
        pass
    
    depth = 0
    start = None
    for i, c in enumerate(text):
        if c == '{':
            if depth == 0:
                start = i
            depth += 1
        elif c == '}':
            depth -= 1
            if depth == 0 and start is not None:
                try:
                    return json.loads(text[start:i+1])
                except:
                    pass
                start = None
    
    raise ValueError("Could not extract JSON")


def build_discord_post(package: dict, target_nation_id: str, state: dict) -> str:
    public_msg = package.get("public_message", "")
    actions = package.get("actions", [])
    
    has_target = any(a.get("target", "none") != "none" for a in actions)
    
    target_name = None
    if has_target:
        target_id = next((a["target"] for a in actions if a["target"] != "none"), None)
        if target_id:
            target_name = next((n["name"] for n in state["nations"] if n["id"] == target_id), target_id)
    
    if target_name:
        msg = f"@{target_name} {public_msg}\n\n"
    else:
        msg = f"{public_msg}\n\n"
    
    msg += "```json\n" + json.dumps(package, indent=2) + "\n```"
    
    return msg


def run_single_turn(turn: int, state: dict, summit_history: list[dict], debug: bool) -> dict:
    """Run one turn and return updated state."""
    print(f"\n--- Turn {turn} ---")
    
    # Each nation takes a turn
    for nation_id in state["turnOrder"]:
        # Prompt nation to produce JSON
        prompt = build_nation_prompt(turn, nation_id, state, summit_history)
        
        nation_run = openclaw_agent(nation_id, prompt, timeout_s=600)
        nation_text = "\n".join(p.get("text", "") for p in nation_run.get("result", {}).get("payloads", []))
        
        try:
            package = extract_json(nation_text)
            print(f"  ✓ {nation_id}")
        except Exception as e:
            print(f"  ✗ {nation_id}: {e}")
            # Skip this nation
            continue
        
        # Post to #summit
        discord_msg = build_discord_post(package, nation_id, state)
        openclaw_message_send("discord", SUMMIT_CHANNEL, discord_msg, account=ACCOUNT_BY_NATION[nation_id])
        
        # Record for next nation
        summit_history.append({
            "author": {"username": {"nation_1": "Hodge", "nation_2": "Aksum", "nation_3": "Urartu"}[nation_id]},
            "content": discord_msg,
            "timestampUtc": now_iso()
        })
        
        # Apply to state
        state = apply_package(state, package)
        
        time.sleep(1)
    
    state["turn"] = turn
    state["updatedAt"] = now_iso()
    
    return state


def build_summary(state: dict, start_turn: int, end_turn: int) -> str:
    """Build a summary message for the batch."""
    lines = [f"⚖️ **Batch Complete: Turns {start_turn}-{end_turn}**\n"]
    
    lines.append("**Final Stats:**")
    for n in state["nations"]:
        lines.append(f"  {n['name']}: T{n['treasury']} F{n['force']} Food{n['food']} S{n['stability']} I{n['industry']}")
    
    lines.append("\n**Final Relations:**")
    for n in state["nations"]:
        for other, score in n["relationships"].items():
            if n["id"] < other:
                other_name = next(o["name"] for o in state["nations"] if o["id"] == other)
                sign = "+" if score > 0 else ""
                lines.append(f"  {n['name']}-{other_name}: {sign}{score}")
    
    if state.get("treaties"):
        lines.append(f"\n**Treaties:** {len(state['treaties'])}")
    if state.get("wars"):
        lines.append(f"**Wars:** {len(state['wars'])}")
    
    return "\n".join(lines)


def main():
    num_turns, debug = parse_args()
    
    print(f"\n=== Batch Run: {num_turns} turns, debug={debug} ===")
    
    state = load_state()
    start_turn = state["turn"] + 1
    
    # Get baseline summit message ID
    data = openclaw_message_read("discord", SUMMIT_CHANNEL, limit=1)
    msgs = data.get("payload", {}).get("messages", [])
    after_id = msgs[0]["id"] if msgs else None
    
    summit_history = []
    
    # Announce batch start
    openclaw_message_send(
        "discord", WORLD_NEWS_CHANNEL,
        f"⚖️ **Batch Run: {num_turns} turns starting** (Turn {start_turn})",
        account=JUDGE_ACCOUNT,
    )
    
    # Run n turns
    for i in range(num_turns):
        turn = start_turn + i
        state = run_single_turn(turn, state, summit_history, debug)
        
        # Persist each turn
        write_json(STATE_PATH, state)
        
        # Log
        log = {
            "turn": turn,
            "generatedAt": now_iso(),
            "state": state,
        }
        write_json(TURN_LOG_DIR / f"turn-{turn:03d}.json", log)
        
        print(f"  → Turn {turn} done")
    
    # Post final summary to #world-news
    summary = build_summary(state, start_turn, start_turn + num_turns - 1)
    openclaw_message_send("discord", WORLD_NEWS_CHANNEL, summary, account=JUDGE_ACCOUNT)
    
    # Also post to #summit
    openclaw_message_send("discord", SUMMIT_CHANNEL, summary, account=JUDGE_ACCOUNT)
    
    print(f"\n=== Batch Complete: {num_turns} turns ===")
    
    if debug:
        print("\n[DEBUG] Final state:")
        print(json.dumps(state, indent=2)[:800] + "...")


if __name__ == "__main__":
    main()