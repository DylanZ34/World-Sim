#!/usr/bin/env python3
"""Run one World Sim turn *through Discord*.

This refines the earlier offline runner:

- Nations publish their packages publicly in #summit (so they can "see" each other)
- The judge gathers packages by reading #summit history
- The judge publishes the turn summary to #world-news

Notes:
- This runner is intentionally *one turn per invocation* to avoid runaway loops.
- It uses OpenClaw CLI commands (message read + agent --deliver).

Prereqs:
- Discord channel ids exist in this guild:
  - #summit: channel:1482491159367389314
  - #world-news: channel:1482491117734985808
- Agent bindings are configured for world_judge + nation_1/2/3.
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


def now_iso():
    return datetime.now(UTC).isoformat()


def sh(cmd: list[str], timeout_s: int = 180):
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_s)
    if proc.returncode != 0:
        raise RuntimeError(
            f"Command failed ({proc.returncode}): {' '.join(cmd)}\nSTDERR:\n{proc.stderr}\nSTDOUT:\n{proc.stdout}"
        )
    return proc.stdout


def openclaw_message_read(channel: str, target: str, limit: int = 10, after: str | None = None):
    cmd = ["openclaw", "message", "read", "--channel", channel, "--target", target, "--limit", str(limit), "--json"]
    if after:
        cmd += ["--after", after]
    out = sh(cmd, timeout_s=180)
    return json.loads(out)


def openclaw_message_send(channel: str, target: str, message: str, reply_to: str | None = None):
    cmd = ["openclaw", "message", "send", "--channel", channel, "--target", target, "--message", message, "--json"]
    if reply_to:
        cmd += ["--reply-to", reply_to]
    out = sh(cmd, timeout_s=180)
    return json.loads(out)


def openclaw_agent_deliver(agent_id: str, message: str, reply_channel: str, reply_to: str, timeout_s: int = 600):
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
        "--json",
        "--timeout",
        str(timeout_s),
    ]
    out = sh(cmd, timeout_s=timeout_s + 30)
    return json.loads(out)


def extract_json(text: str):
    text = text.strip()
    try:
        return json.loads(text)
    except Exception:
        pass

    # try fenced block first
    m = re.search(r"```(?:json)?\s*(\{.*?\}|\[.*?\])\s*```", text, flags=re.S)
    if m:
        return json.loads(m.group(1))

    # fallback: last json-ish object
    starts = [m.start() for m in re.finditer(r"[\{\[]", text)]
    for start in sorted(starts, reverse=True):
        snippet = text[start:]
        for end in range(len(snippet), 0, -1):
            cand = snippet[:end].rstrip()
            if not (cand.endswith("}") or cand.endswith("]")):
                continue
            try:
                return json.loads(cand)
            except Exception:
                continue

    raise ValueError("Could not extract JSON")


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
        "You must publish your response into #summit as ONE message with:\n"
        "1) 1-3 lines of in-character public statement\n"
        "2) then a JSON code block with your turn package\n\n"
        "Example format:\n"
        "Public statement...\n"
        "```json\n{...}\n```\n\n"
        f"Schema (must follow exactly):\n{schema}\n\n"
        f"Canonical state (publicly visible for this MVP):\n{briefing}\n"
    )


def judge_prompt(turn: int, before_state: dict, summit_messages: list[dict]) -> str:
    judge_proc = load_text(RULES_DIR / "judge-procedure.md")
    schema = load_text(RULES_DIR / "action-schema.md")
    judge_prompt_md = load_text(ROOT / "prompts" / "judge-turn-prompt.md")

    transcript = [
        {
            "id": m.get("id"),
            "author": m.get("author", {}).get("username"),
            "authorId": m.get("author", {}).get("id"),
            "content": m.get("content"),
            "timestampUtc": m.get("timestampUtc"),
        }
        for m in summit_messages
    ]

    return (
        f"{judge_prompt_md}\n\n"
        f"## Rules\n{judge_proc}\n\n"
        f"## Action schema\n{schema}\n\n"
        f"## BEFORE state\n{json.dumps(before_state, indent=2)}\n\n"
        "## #summit transcript since turn start\n"
        f"{json.dumps(transcript, indent=2)}\n\n"
        "## Output requirements (JSON only)\n"
        "Return a single JSON object with keys:\n"
        "- updatedWorldState\n"
        "- publicSummaryLines (array of strings)\n"
        "- judgeNotes (array of strings)\n"
        "No markdown."
    )


def main():
    state = load_state()
    before = deepcopy(state)
    turn = before["turn"] + 1

    # Mark a baseline in summit so we know where to read from.
    after_id = get_latest_message_id(SUMMIT_CHANNEL)

    # Announce turn start publicly.
    openclaw_message_send(
        "discord",
        WORLD_NEWS_CHANNEL,
        f"[TURN {turn} START] Nations will post their public statements + packages in #summit."
    )

    # Prompt each nation (deliver their prompt into #summit so it's public).
    for nid in before["turnOrder"]:
        openclaw_agent_deliver(
            nid,
            nation_prompt(turn, nid, before),
            reply_channel="discord",
            reply_to=SUMMIT_CHANNEL,
            timeout_s=600,
        )

    # Collect summit messages until we have 3 valid packages.
    packages = {}
    summit_seen = []
    poll_after = after_id

    deadline = time.time() + 300  # 5 min
    while time.time() < deadline and len(packages) < 3:
        data = openclaw_message_read("discord", SUMMIT_CHANNEL, limit=50, after=poll_after)
        msgs = data.get("payload", {}).get("messages", [])
        if msgs:
            poll_after = msgs[0]["id"]  # newest in this batch (discord returns newest->older)
            summit_seen.extend(msgs)

            for m in msgs:
                author = m.get("author", {})
                username = author.get("username")
                content = m.get("content") or ""

                # identify nation by username (bot names)
                nation_id = None
                if username == "Hodge":
                    nation_id = "nation_1"
                elif username == "Aksum":
                    nation_id = "nation_2"
                elif username == "Urartu":
                    nation_id = "nation_3"

                if not nation_id or nation_id in packages:
                    continue

                try:
                    pkg = extract_json(content)
                    # minimal check
                    if pkg.get("turn") == turn and pkg.get("nation") == nation_id:
                        packages[nation_id] = pkg
                except Exception:
                    continue

        if len(packages) < 3:
            time.sleep(3)

    if len(packages) < 3:
        raise RuntimeError(f"Timed out waiting for nation packages; got {list(packages.keys())}")

    # Ask judge to adjudicate based on the summit transcript.
    judge_run = openclaw_agent_deliver(
        "world_judge",
        judge_prompt(turn, before, summit_seen),
        reply_channel="discord",
        reply_to=WORLD_NEWS_CHANNEL,
        timeout_s=900,
    )

    judge_text = "\n".join(p.get("text") or "" for p in judge_run.get("result", {}).get("payloads", []))
    judge_json = extract_json(judge_text)

    updated = judge_json.get("updatedWorldState")
    if not updated:
        raise ValueError("Judge output missing updatedWorldState")

    updated["turn"] = turn
    updated["status"] = "running"
    updated["updatedAt"] = now_iso()

    # Persist canonical state + log.
    write_json(STATE_PATH, updated)

    log = {
        "turn": turn,
        "generatedAt": now_iso(),
        "summitAfterId": after_id,
        "summitMessages": summit_seen,
        "packages": [packages[n] for n in before["turnOrder"]],
        "judge": judge_json,
        "before": before,
        "after": updated,
    }
    write_json(TURN_LOG_DIR / f"turn-{turn:03d}.json", log)

    print(f"Discord turn {turn} completed.")


if __name__ == "__main__":
    main()
