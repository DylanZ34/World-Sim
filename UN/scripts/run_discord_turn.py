#!/usr/bin/env python3
"""Run one World Sim turn through Discord with debug mode enabled.

Flow:
- Nations post in #summit (addressed to target or as general announcements)
- Judge reads #summit to gather packages
- Judge posts turn summary + debug JSON to #world-news

Debug mode is ON: judge shows full JSON in #world-news.
"""

import json
import re
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

NATION_IDS = ["nation_1", "nation_2", "nation_3"]

# Account IDs for each bot (must match binding in OpenClaw)
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
        raise RuntimeError(
            f"Command failed ({proc.returncode}): {' '.join(cmd)}\nSTDERR:\n{proc.stderr}\nSTDOUT:\n{proc.stdout}"
        )
    return proc.stdout


def openclaw_message_read(channel: str, target: str, limit: int = 20, after: str | None = None, before: str | None = None):
    cmd = ["openclaw", "message", "read", "--channel", channel, "--target", target, "--limit", str(limit), "--json"]
    if after:
        cmd += ["--after", after]
    if before:
        cmd += ["--before", before]
    out = sh(cmd, timeout_s=180)
    return json.loads(out)


def openclaw_message_send(channel: str, target: str, message: str, account: str | None = None, reply_to: str | None = None):
    cmd = ["openclaw", "message", "send", "--channel", channel, "--target", target, "--message", message]
    if account:
        cmd += ["--account", account]
    if reply_to:
        cmd += ["--reply-to", reply_to]
    cmd += ["--json"]
    out = sh(cmd, timeout_s=180)
    return json.loads(out)


def openclaw_agent_deliver(agent_id: str, message: str, reply_channel: str, reply_to: str, reply_account: str, timeout_s: int = 600):
    cmd = [
        "openclaw",
        "agent",
        "--agent",
        agent_id,
        "--message",
        message,
        "--deliver",
        "--reply-channel",
        reply_channel,
        "--reply-to",
        reply_to,
        "--reply-account",
        reply_account,
        "--json",
        "--timeout",
        str(timeout_s),
    ]
    out = sh(cmd, timeout_s=timeout_s + 30)
    return json.loads(out)


def extract_json_from_content(full_text: str, turn: int, nation_id: str):
    """Extract a valid JSON turn package from potentially multi-message content."""
    text = full_text.strip()
    
    # Strategy 1: Look for a complete JSON block wrapped in ```json...```
    # This is the most reliable if the model follows instructions
    json_blocks = re.findall(r"```json\s*(\{[\s\S]*?\})\s*```", text)
    for block in json_blocks:
        try:
            pkg = json.loads(block)
            if pkg.get("turn") == turn and pkg.get("nation") == nation_id:
                if "actions" in pkg and isinstance(pkg.get("actions"), list) and len(pkg["actions"]) == 2:
                    return pkg
        except Exception:
            continue
    
    # Strategy 2: Look for any JSON object that looks like a turn package
    # Find all { ... } patterns and try to parse them
    # Look for the one with "turn", "nation", "actions"
    candidates = []
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
                candidate = text[start:i+1]
                try:
                    pkg = json.loads(candidate)
                    if "turn" in pkg and "nation" in pkg and "actions" in pkg:
                        candidates.append((len(candidate), pkg))
                except Exception:
                    pass
                start = None
    
    # Try the largest candidate that matches
    candidates.sort(key=lambda x: x[0], reverse=True)
    for _, pkg in candidates:
        if pkg.get("turn") == turn and pkg.get("nation") == nation_id:
            actions = pkg.get("actions")
            if isinstance(actions, list) and len(actions) == 2:
                return pkg
    
    # Strategy 3: desperation - look for any JSON with turn and nation fields
    try:
        # Try the whole text as JSON
        pkg = json.loads(text)
        if pkg.get("turn") == turn and pkg.get("nation") == nation_id:
            return pkg
    except Exception:
        pass
    
    raise ValueError("Could not extract valid turn package")


def load_text(path: Path) -> str:
    return path.read_text()


def load_state():
    return json.loads(STATE_PATH.read_text())


def write_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n")


def get_latest_message_id(channel_target: str) -> str | None:
    data = openclaw_message_read("discord", channel_target, limit=1)
    msgs = data.get("payload", {}).get("messages", [])
    if not msgs:
        return None
    return msgs[0]["id"]


def nation_prompt(turn: int, nation_id: str, state_before: dict) -> str:
    schema = load_text(RULES_DIR / "action-schema.md")
    nation_prompt_md = load_text(ROOT / "prompts" / "nation-turn-prompt.md")
    briefing = json.dumps(state_before, indent=2)

    return (
        f"{nation_prompt_md}\n\n"
        f"Turn: {turn}\nNation id: {nation_id}\n\n"
        "## Output format (CRITICAL)\n"
        "You must produce exactly ONE message. Not two. ONE message.\n"
        "The message should contain:\n"
        "1. A short public statement (1-3 lines). If any of your 2 actions target another nation, ADDRESS that nation by name at the start.\n"
        "   - If targeting: \"@Urartu, we propose...\"\n"
        "   - If no target: just your statement as a general announcement.\n"
        "2. Then a ```json``` code block with your full turn package (exactly 2 actions).\n"
        "3. NOTHING ELSE - do not send multiple messages.\n\n"
        "Example of ONE message:\n"
        "\"@Urartu, we propose a border conduct memorandum. We believe stability serves all.\n```json\n{\n  \"turn\": 6,\n  \"nation\": \"nation_1\",\n  \"risk\": \"medium\",\n  \"public_message\": \"...\",\n  \"actions\": [...]\n}\n```\"\n\n"
        f"Schema:\n{schema}\n\n"
        f"Canonical state (public):\n{briefing}\n"
    )


def judge_prompt(turn: int, before_state: dict, summit_messages: list[dict]) -> str:
    judge_proc = load_text(RULES_DIR / "judge-procedure.md")
    schema = load_text(RULES_DIR / "action-schema.md")
    judge_prompt_md = load_text(ROOT / "prompts" / "judge-turn-prompt.md")

    # Sort messages oldest first
    sorted_msgs = sorted(summit_messages, key=lambda m: m.get("timestampUtc", ""))

    transcript = [
        {
            "id": m.get("id"),
            "author": m.get("author", {}).get("username"),
            "authorId": m.get("author", {}).get("id"),
            "content": m.get("content"),
            "timestampUtc": m.get("timestampUtc"),
        }
        for m in sorted_msgs
    ]

    return (
        f"{judge_prompt_md}\n\n"
        f"## Rules\n{judge_proc}\n\n"
        f"## Action schema\n{schema}\n\n"
        f"## BEFORE state\n{json.dumps(before_state, indent=2)}\n\n"
        "## #summit transcript (all messages since turn start, oldest first)\n"
        f"{json.dumps(transcript, indent=2)}\n\n"
        "## Output requirements (JSON only)\n"
        "Return a single JSON object with keys:\n"
        "- updatedWorldState\n"
        "- publicSummaryLines (array of strings suitable for Discord)\n"
        "- judgeNotes (array of strings)\n"
        "No markdown outside JSON."
    )


def collect_nation_packages(summit_msgs: list[dict], turn: int) -> dict:
    """Collect messages by nation, group sequential messages from same author, extract JSON."""
    # Sort by timestamp ascending
    sorted_msgs = sorted(summit_msgs, key=lambda m: m.get("timestampUtc", ""))

    # Group by author
    by_author = {}
    for m in sorted_msgs:
        author = m.get("author", {}).get("username")
        if not author:
            continue
        by_author.setdefault(author, []).append(m)

    # Map usernames to nation IDs
    USER_TO_NATION = {"Hodge": "nation_1", "Aksum": "nation_2", "Urartu": "nation_3"}

    packages = {}

    for username, msgs in by_author.items():
        nation_id = USER_TO_NATION.get(username)
        if not nation_id:
            continue

        # Concatenate content from all messages from this author (in order)
        combined_content = "\n".join(m.get("content", "") for m in msgs)

        try:
            pkg = extract_json_from_content(combined_content, turn, nation_id)
            packages[nation_id] = pkg
            print(f"✓ Extracted package for {nation_id} from {len(msgs)} message(s)")
        except Exception as e:
            print(f"✗ {nation_id}: failed to extract JSON: {e}")
            # Print a bit more of the content for debugging
            preview = combined_content[:400].replace('\n', ' ')
            print(f"   Preview: {preview}...")

    return packages


def main():
    state = load_state()
    before = deepcopy(state)
    turn = before["turn"] + 1

    # Mark baseline to read after.
    after_id = get_latest_message_id(SUMMIT_CHANNEL)

    # Announce turn start.
    openclaw_message_send(
        "discord",
        WORLD_NEWS_CHANNEL,
        f"⚖️ **[TURN {turn} START]** Nations, submit your packages in #summit now.",
        account=JUDGE_ACCOUNT,
    )

    # Prompt each nation (deliver to #summit via their correct bot account).
    for nid in before["turnOrder"]:
        openclaw_agent_deliver(
            nid,
            nation_prompt(turn, nid, before),
            reply_channel="discord",
            reply_to=SUMMIT_CHANNEL,
            reply_account=ACCOUNT_BY_NATION[nid],
            timeout_s=600,
        )

    # Poll #summit until we have 3 valid packages OR timeout.
    # Wait for messages to settle (no new messages for a few seconds)
    packages = {}
    summit_seen = []
    poll_after = after_id
    last_new_count = 0
    no_new_counter = 0

    deadline = time.time() + 300  # 5 min max
    while time.time() < deadline:
        # Read messages AFTER the turn start marker
        data = openclaw_message_read("discord", SUMMIT_CHANNEL, limit=50, after=poll_after)
        msgs = data.get("payload", {}).get("messages", [])
        
        if msgs:
            # Messages come newest-first
            poll_after = msgs[0]["id"]
            # Add in reverse to keep oldest-first
            new_msgs = [m for m in msgs if m["id"] not in {x["id"] for x in summit_seen}]
            if new_msgs:
                summit_seen = new_msgs + summit_seen
                no_new_counter = 0
            else:
                no_new_counter += 1
            
            # Try to extract packages
            packages = collect_nation_packages(summit_seen, turn)
            
            if len(packages) >= 3:
                break
                
            # If we haven't seen new messages for 2 consecutive checks, wait a bit more
            if no_new_counter >= 2 and len(packages) < 3:
                # Wait a bit longer for more messages
                time.sleep(5)
                no_new_counter = 0
        else:
            time.sleep(2)

        if len(packages) >= 3:
            break
            
        time.sleep(2)

    if len(packages) < 3:
        print(f"Warning: only got packages for {list(packages.keys())}")
        if not packages:
            raise RuntimeError(f"Timed out waiting for nation packages; got {list(packages.keys())}")

    # Judge adjudicates.
    print(f"\nProceeding to judge with packages: {list(packages.keys())}")
    judge_run = openclaw_agent_deliver(
        "world_judge",
        judge_prompt(turn, before, summit_seen),
        reply_channel="discord",
        reply_to=WORLD_NEWS_CHANNEL,
        reply_account=JUDGE_ACCOUNT,
        timeout_s=900,
    )

    judge_text = "\n".join(p.get("text") or "" for p in judge_run.get("result", {}).get("payloads", []))
    judge_json = extract_json_from_content(judge_text, turn, "world_judge")  # Reuse the robust extractor

    # Handle case where judge didn't return a proper structure
    if "updatedWorldState" not in judge_json:
        # Try to find it differently
        raise ValueError(f"Judge output missing updatedWorldState. Got keys: {list(judge_json.keys())}")

    updated = judge_json.get("updatedWorldState")
    if not updated:
        raise ValueError("Judge output missing updatedWorldState")

    updated["turn"] = turn
    updated["status"] = "running"
    updated["updatedAt"] = now_iso()

    # Persist state + log.
    write_json(STATE_PATH, updated)

    log = {
        "turn": turn,
        "generatedAt": now_iso(),
        "summitAfterId": after_id,
        "summitMessages": summit_seen,
        "packages": [packages[n] for n in before["turnOrder"] if n in packages],
        "judge": judge_json,
        "before": before,
        "after": updated,
    }
    write_json(TURN_LOG_DIR / f"turn-{turn:03d}.json", log)

    # Print result to console.
    summary_lines = judge_json.get("publicSummaryLines", [])
    print(f"\n=== Turn {turn} completed ===")
    for line in summary_lines[:6]:
        print(line)
    if DEBUG:
        print("\n[DEBUG] Full JSON:")
        print(json.dumps(judge_json, indent=2)[:800] + "...")


if __name__ == "__main__":
    main()