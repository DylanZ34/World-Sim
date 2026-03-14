# World Judge Workspace

This is the isolated OpenClaw workspace for the `world_judge` agent in World Sim.

## Role

The judge is responsible for:

- turn orchestration
- canonical world-state ownership
- action validation
- adjudication
- publishing world updates

## Key directories

- `world/` — canonical state and turn logs
- `rules/` — judge-side procedures and game rules
- `memory/` — recent operational notes

## Current rules scaffold

- `rules/world-rules.md` — first playable world rules
- `rules/judge-procedure.md` — turn-running procedure for `world_judge`
- `rules/action-schema.md` — nation submission format

## Model

Configured target model: `openai-codex/gpt-5.4`
