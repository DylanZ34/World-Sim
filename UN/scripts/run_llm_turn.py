#!/usr/bin/env python3
"""Run one World Sim turn using actual OpenClaw agents.

Flow:
- load canonical state (judge workspace)
- ask each nation agent to output a JSON turn package (schema: rules/action-schema.md)
- ask world_judge to adjudicate and output updated canonical state + a public summary
- persist:
  - UN/world/world-state.json
  - UN/world/turn-log/turn-XXX.json

This is intentionally single-turn and manual-triggered to avoid runaway loops.
"""

import json
import re
import subprocess
from copy import deepcopy
from datetime import datetime, UTC
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE_PATH = ROOT / "world" / "world-state.json"
TURN_LOG_DIR = ROOT / "world" / "turn-log"
RULES_DIR = ROOT / "rules"

NATIONS = ["nation_1", "nation_2", "nation_3"]


def now_iso():
    return datetime.now(UTC).isoformat()


def load_text(path: Path) -> str:
    return path.read_text()


def load_state():
    return json.loads(STATE_PATH.read_text())


def write_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n")


def extract_json(text: str):
    """Best-effort extraction of a JSON object/array from an LLM reply."""
    text = text.strip()

    # Fast path: whole text is json.
    try:
        return json.loads(text)
    except Exception:
        pass

    # Try to find the last JSON object/array in the text.
    candidates = []

    # Objects
    for m in re.finditer(r"\{", text):
        candidates.append(m.start())
    # Arrays
    for m in re.finditer(r"\[", text):
        candidates.append(m.start())

    candidates = sorted(set(candidates), reverse=True)

    for start in candidates:
        snippet = text[start:]
        # Heuristic: trim leading junk before first bracket, then try shrinking from end.
        end = len(snippet)
        while end > 0:
            tail = snippet[:end].rstrip()
            # require it ends sensibly
            if not (tail.endswith("}") or tail.endswith("]")):
                end -= 1
                continue
            try:
                return json.loads(tail)
            except Exception:
                end -= 1

    raise ValueError("Could not extract valid JSON from reply")


def openclaw_agent(agent_id: str, message: str, timeout_s: int = 600) -> dict:
    """Run a single agent turn via the Gateway and return the CLI JSON."""
    cmd = [
        "openclaw",
        "agent",
        "--agent",
        agent_id,
        "--message",
        message,
        "--json",
        "--timeout",
        str(timeout_s),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(
            f"openclaw agent failed for {agent_id} (code {proc.returncode})\nSTDERR:\n{proc.stderr}\nSTDOUT:\n{proc.stdout}"
        )
    return json.loads(proc.stdout)


def get_reply_text(run_json: dict) -> str:
    payloads = run_json.get("result", {}).get("payloads", [])
    if not payloads:
        return ""
    return "\n".join(p.get("text") or "" for p in payloads).strip()


def validate_package(pkg: dict, turn: int, nation_id: str):
    required = {"turn", "nation", "risk", "public_message", "actions"}
    missing = required - set(pkg.keys())
    if missing:
        raise ValueError(f"{nation_id} package missing keys: {sorted(missing)}")
    if pkg["turn"] != turn:
        raise ValueError(f"{nation_id} package turn mismatch: {pkg['turn']} != {turn}")
    if pkg["nation"] != nation_id:
        raise ValueError(f"{nation_id} package nation mismatch: {pkg['nation']} != {nation_id}")
    if pkg["risk"] not in {"low", "medium", "high"}:
        raise ValueError(f"{nation_id} invalid risk: {pkg['risk']}")
    actions = pkg["actions"]
    if not isinstance(actions, list) or len(actions) != 2:
        raise ValueError(f"{nation_id} must submit exactly 2 actions")
    for a in actions:
        for k in ["type", "target", "summary", "intensity"]:
            if k not in a:
                raise ValueError(f"{nation_id} action missing {k}: {a}")
        if a["intensity"] not in {"low", "medium", "high"}:
            raise ValueError(f"{nation_id} invalid intensity: {a['intensity']}")


def clamp_stat(v):
    return max(0, min(10, int(v)))


def clamp_rel(v):
    return max(-5, min(5, int(v)))


def validate_state(state: dict):
    # Minimal, v0.1-specific validation.
    if not isinstance(state.get("turn"), int):
        raise ValueError("state.turn must be int")
    if "nations" not in state or not isinstance(state["nations"], list):
        raise ValueError("state.nations missing or invalid")

    by_id = {n["id"]: n for n in state["nations"]}
    for nid in NATIONS:
        if nid not in by_id:
            raise ValueError(f"missing nation {nid} in state")

    for n in state["nations"]:
        for stat in ["treasury", "force", "food", "stability", "industry"]:
            n[stat] = clamp_stat(n.get(stat, 0))
        if "relationships" in n:
            for other in list(n["relationships"].keys()):
                n["relationships"][other] = clamp_rel(n["relationships"][other])


def build_briefing(state: dict) -> str:
    nation_lines = []
    for n in state["nations"]:
        nation_lines.append(
            f"- {n['id']} ({n.get('name','')}): T{n['treasury']} F{n['force']} Food{n['food']} S{n['stability']} I{n['industry']} | rel {n['relationships']}"
        )
    treaties = state.get("treaties", [])
    wars = state.get("wars", [])
    events = state.get("publicEvents", [])
    tail_events = events[-6:] if events else []

    return "\n".join(
        [
            f"TURN {state['turn']} PUBLIC BRIEFING",
            "Nation snapshot:",
            *nation_lines,
            f"Treaties: {treaties}",
            f"Wars/Crisis: {wars}",
            "Recent public events:",
            *(f"- {e}" for e in tail_events),
        ]
    )


def nation_message(turn: int, nation_id: str, briefing: str) -> str:
    schema = load_text(RULES_DIR / "action-schema.md")
    prompt = load_text(ROOT / "prompts" / "nation-turn-prompt.md")
    return (
        f"{prompt}\n\n"
        f"## Current turn\nTurn is {turn}. Your nation id is {nation_id}.\n\n"
        f"## Public world briefing\n{briefing}\n\n"
        f"## Schema (must follow exactly)\n{schema}\n\n"
        "Return JSON only. No preamble. No markdown."
    )


def judge_message(turn: int, prior_state: dict, packages: list[dict]) -> str:
    judge_proc = load_text(RULES_DIR / "judge-procedure.md")
    schema = load_text(RULES_DIR / "action-schema.md")
    judge_prompt = load_text(ROOT / "prompts" / "judge-turn-prompt.md")

    return (
        f"{judge_prompt}\n\n"
        f"## Rules\n{judge_proc}\n\n"
        f"## Action schema\n{schema}\n\n"
        f"## Current canonical state (BEFORE turn {turn})\n"
        f"{json.dumps(prior_state, indent=2)}\n\n"
        f"## Submitted nation packages for turn {turn}\n"
        f"{json.dumps(packages, indent=2)}\n\n"
        "## Output requirements (JSON only)\n"
        "Return a single JSON object with keys:\n"
        "- updatedWorldState (full canonical state AFTER adjudication)\n"
        "- publicSummaryLines (array of strings suitable for Discord)\n"
        "- judgeNotes (array of short strings)\n"
        "- deltas (object: optional, any structure you like)\n"
        "No markdown. No prose outside JSON."
    )


def main():
    state = load_state()
    before = deepcopy(state)

    turn = state["turn"] + 1
    state["turn"] = turn

    briefing = build_briefing(before)

    packages = []
    raw_replies = {}

    for nid in before["turnOrder"]:
        msg = nation_message(turn, nid, briefing)
        run = openclaw_agent(nid, msg, timeout_s=600)
        reply_text = get_reply_text(run)
        raw_replies[nid] = reply_text
        pkg = extract_json(reply_text)
        validate_package(pkg, turn, nid)
        packages.append(pkg)

    judge_run = openclaw_agent("world_judge", judge_message(turn, before, packages), timeout_s=900)
    judge_text = get_reply_text(judge_run)
    judge_json = extract_json(judge_text)

    updated = judge_json.get("updatedWorldState")
    if not updated:
        raise ValueError("Judge output missing updatedWorldState")

    # Enforce turn number and updatedAt
    updated["turn"] = turn
    updated["status"] = "running"
    updated["updatedAt"] = now_iso()
    validate_state(updated)

    summary_lines = judge_json.get("publicSummaryLines", [])
    if not isinstance(summary_lines, list) or not all(isinstance(s, str) for s in summary_lines):
        summary_lines = ["(judge produced no usable public summary)"]

    # Persist canonical state
    write_json(STATE_PATH, updated)

    # Persist turn log
    TURN_LOG_DIR.mkdir(parents=True, exist_ok=True)
    log = {
        "turn": turn,
        "generatedAt": now_iso(),
        "before": before,
        "packages": packages,
        "rawNationReplies": raw_replies,
        "judge": judge_json,
        "publicSummaryLines": summary_lines,
        "after": updated,
    }
    write_json(TURN_LOG_DIR / f"turn-{turn:03d}.json", log)

    print(f"LLM turn {turn} completed.")
    for line in summary_lines:
        print(line)


if __name__ == "__main__":
    main()
