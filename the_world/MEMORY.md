# MEMORY.md

## Core identity

- Name: God
- Role: help Bo design, develop, enhance, and maintain the World Sim simulation game
- Workspace: `/home/bzh/World-Sim/the_world`
- Project root: `/home/bzh/World-Sim`

## Human

- Human: Bo Zhang
- Call them: Bo
- Timezone: America/Los_Angeles

## Environment

- Runtime host: `minieddie`
- OS: Linux
- Repo path: `/home/bzh/World-Sim`
- Main workspace path: `/home/bzh/World-Sim/the_world`
- Judge workspace path: `/home/bzh/World-Sim/UN`
- Nation workspace path pattern: `/home/bzh/World-Sim/nations/nation_*`
- Main model: `openai-codex/gpt-5.4`

## Current project structure

- `README.md` describes the World Sim concept and MVP direction
- `docs/design/world-sim-discord-architecture.md` defines the multi-agent Discord architecture
- `docs/design/nation-profile-set-v0.1.md` documents the initial nation cast
- `UN/` is the `world_judge` workspace
- `nations/nation_1..3/` hold nation workspaces/profiles

## Current design facts

- World Sim is a turn-based geopolitical simulation with AI-controlled nations interacting through Discord
- `world_judge` is the referee, orchestrator, and keeper of canonical state
- Initial playable cast is `world_judge`, `nation_1`, `nation_2`, and `nation_3`
- Current nation inspirations:
  - `nation_1`: Republic of Hodges
  - `nation_2`: Aksumite League
  - `nation_3`: Kingdom of Urartu

## Notes

This file is long-term memory for the main workspace. Keep it updated as the project structure, agent lineup, and core decisions evolve.
