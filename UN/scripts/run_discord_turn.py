#!/usr/bin/env python3
"""Run World Sim turn - nation produces JSON, script posts to Discord.

Flow:
- For each nation in turn order:
  1. Judge shares public state + summit mentions to nation
  2. Nation produces JSON package (not posted to Discord)
  3. Script posts the package to #summit (addressed if target, general if none)
  4. Script applies to state
- After all nations, post final public state to #summit

This avoids the split-message issue by not having agents post directly.
"""

import json
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

ACCOUNT_BY_NATION = {
    "nation_1": "nation1bot",
    "nation_2": "nation2bot",
    "nation_3": "nation3bot",
}
JUDGE_ACCOUNT = "judgebot"

DEBUG = True


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
    """Run agent and get JSON response (no Discord posting)."""
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
    """Extract public state for nations."""
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
    """Apply a nation's package to state."""
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
    
    # Update treaties/wars
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
    """Build prompt for nation to produce JSON (no Discord posting)."""
    schema = load_text(RULES_DIR / "action-schema.md")
    nation_prompt_md = load_text(ROOT / "prompts" / "nation-turn-prompt.md")
    public_state = get_public_state(state)
    state_json = json.dumps(public_state, indent=2)
    
    # Get messages addressed to this nation
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
    """Extract JSON from agent response."""
    import re
    
    text = text.strip()
    
    # Try ```json blocks
    blocks = re.findall(r"```json\s*([\s\S]*?)```", text)
    for block in blocks:
        try:
            return json.loads(block.strip())
        except:
            pass
    
    # Try raw JSON
    try:
        return json.loads(text)
    except:
        pass
    
    # Find any JSON-like object
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
    """Build the Discord message for a nation's package."""
    public_msg = package.get("public_message", "")
    actions = package.get("actions", [])
    
    # Determine if any action has a target
    has_target = any(a.get("target", "none") != "none" for a in actions)
    
    # Find target nation name if any
    target_name = None
    if has_target:
        target_id = next((a["target"] for a in actions if a["target"] != "none"), None)
        if target_id:
            target_name = next((n["name"] for n in state["nations"] if n["id"] == target_id), target_id)
    
    # Build message
    if target_name:
        msg = f"@{target_name} {public_msg}\n\n"
    else:
        msg = f"{public_msg}\n\n"
    
    msg += "```json\n" + json.dumps(package, indent=2) + "\n```"
    
    return msg


def main():
    state = load_state()
    before = deepcopy(state)
    turn = state["turn"] + 1
    
    print(f"\n=== Starting Turn {turn} ===")
    
    # Announce turn start
    openclaw_message_send(
        "discord", WORLD_NEWS_CHANNEL,
        f"⚖️ **[TURN {turn} START]** Sequential turns beginning.",
        account=JUDGE_ACCOUNT,
    )
    
    # Get baseline summit message ID
    data = openclaw_message_read("discord", SUMMIT_CHANNEL, limit=1)
    msgs = data.get("payload", {}).get("messages", [])
    after_id = msgs[0]["id"] if msgs else None
    
    summit_history = []
    
    # Each nation takes a turn
    for nation_id in state["turnOrder"]:
        print(f"\n--- {nation_id} turn ---")
        
        # Prompt nation to produce JSON
        prompt = build_nation_prompt(turn, nation_id, state, summit_history)
        
        nation_run = openclaw_agent(nation_id, prompt, timeout_s=600)
        nation_text = "\n".join(p.get("text", "") for p in nation_run.get("result", {}).get("payloads", []))
        
        # Extract JSON
        try:
            package = extract_json(nation_text)
            print(f"✓ Got package from {nation_id}")
        except Exception as e:
            print(f"✗ Failed to extract JSON: {e}")
            raise RuntimeError(f"Could not get valid package from {nation_id}")
        
        # Post to #summit on behalf of nation
        discord_msg = build_discord_post(package, nation_id, state)
        openclaw_message_send(
            "discord", SUMMIT_CHANNEL,
            discord_msg,
            account=ACCOUNT_BY_NATION[nation_id],
        )
        print(f"✓ Posted to #summit")
        
        # Record in summit history for next nation
        summit_history.append({
            "author": {"username": {"nation_1": "Hodge", "nation_2": "Aksum", "nation_3": "Urartu"}[nation_id]},
            "content": discord_msg,
            "timestampUtc": now_iso()
        })
        
        # Apply to state
        state = apply_package(state, package)
        print(f"✓ Applied to state")
        
        # Brief pause
        time.sleep(2)
    
    # All done - update turn number and post final state
    state["turn"] = turn
    state["status"] = "running"
    state["updatedAt"] = now_iso()
    
    # Post final public state to summit
    public_state = get_public_state(state)
    lines = [f"⚖️ **Turn {turn} Complete**\n"]
    lines.append("**Stats:**")
    for n in public_state["nations"]:
        lines.append(f"  {n['name']}: T{n['treasury']} F{n['force']} Food{n['food']} S{n['stability']} I{n['industry']}")
    
    lines.append("\n**Relations:**")
    for n in public_state["nations"]:
        for other, score in n["relationships"].items():
            if n["id"] < other:
                other_name = next(o["name"] for o in public_state["nations"] if o["id"] == other)
                lines.append(f"  {n['name']}-{other_name}: {score}")
    
    if public_state.get("treaties"):
        lines.append(f"\n**Treaties:** {len(public_state['treaties'])}")
    if public_state.get("wars"):
        lines.append(f"**Wars:** {len(public_state['wars'])}")
    
    openclaw_message_send("discord", SUMMIT_CHANNEL, "\n".join(lines), account=JUDGE_ACCOUNT)
    
    # Persist
    write_json(STATE_PATH, state)
    log = {
        "turn": turn,
        "generatedAt": now_iso(),
        "before": before,
        "after": state,
        "summitMessages": summit_history,
    }
    write_json(TURN_LOG_DIR / f"turn-{turn:03d}.json", log)
    
    print(f"\n=== Turn {turn} completed ===")
    if DEBUG:
        print(json.dumps(state, indent=2)[:500] + "...")


if __name__ == "__main__":
    main()