# World Sim

World Sim is a turn-based geopolitical simulation in which AI-controlled nations interact through Discord.

The project is designed around a small cast of agent actors that behave like nations in a strategy game inspired by **Civilization**:

- a `world_judge` agent acts as referee, orchestrator, and keeper of the canonical world state
- multiple nation agents act as sovereign powers with distinct goals, personalities, and strategies
- all actors appear in the same Discord server as separate bot identities
- the simulation advances in explicit turns rather than chaotic free-form chatter

## Current design direction

The current MVP direction is:

- **multi-bot Discord setup**: one Discord bot account per in-world actor
- **multi-agent OpenClaw architecture**: one OpenClaw agent per actor
- **turn-based gameplay**: the world advances round by round
- **judge-mediated flow**: `world_judge` controls turn progression and adjudication
- **explicit trigger rules**: nation agents speak only when allowed by the game structure

Initial actor set:

- `world_judge`
- `nation_1`
- `nation_2`
- `nation_3`

## Project goals

- simulate diplomacy, rivalry, conflict, and cooperation among AI nations
- give each nation a distinct identity and strategic doctrine
- create a shared public stage in Discord where all actors can visibly interact
- maintain a coherent canonical world state across turns
- avoid runaway bot loops and uncontrolled chatter
- provide a foundation that can grow into a richer world simulation over time

## How the simulation works

At a high level, each turn follows a structured loop:

1. `world_judge` starts the turn and announces the current situation
2. each nation is prompted in turn to submit its actions
3. nation agents respond with one turn package each
4. `world_judge` adjudicates outcomes and updates world state
5. `world_judge` publishes the results and starts the next turn when ready

This makes the system easier to reason about, test, and expand.

## Why Discord

Discord is the social stage for the simulation:

- each actor can have its own visible bot identity
- public diplomacy can happen in shared channels
- the world can be observed like a live strategy roleplay
- private or nation-specific channels can be added later if needed

## Proposed Discord structure

Public channels:

- `#world-news` — official announcements, turn summaries, world events
- `#summit` — diplomacy and public nation-to-nation interaction
- `#rules-and-status` — pinned rules, current turn, and status summaries

Optional future private channels:

- `#nation-1-private`
- `#nation-2-private`
- `#nation-3-private`

## Architecture choices

This project currently adopts:

- **Option B** — multiple Discord bot accounts, one per actor
- **Mechanism 3** — explicit trigger rules to control when each actor may speak

That means the system is optimized for:

- visible multi-party interaction in the same server
- strong identity separation between actors
- clear control over turn-taking
- protection against bots triggering each other endlessly

## Repository roadmap

Near-term work includes:

- define the OpenClaw config for multiple Discord bot accounts
- create the workspace skeleton for `world_judge` and each nation
- write nation profiles, goals, and strategic doctrines
- define the game rules and legal turn actions
- implement canonical world-state storage
- test the first playable 3-nation simulation loop

## Design docs

See:

- `docs/design/world-sim-discord-architecture.md`
- `docs/design/nation-profile-set-v0.1.md`

## MVP principles

For the first version, the project should stay focused on:

- 1 judge
- 3 nations
- 1 shared Discord server
- turn-based progression
- simple but distinct nation behavior
- clear adjudication and state updates

Not in MVP:

- uncontrolled real-time autonomous chatter
- large numbers of nations
- overly complex combat/economy systems
- deeply hidden-information-heavy gameplay

## Vision

The long-term vision is a world of agent nations that feels alive, strategic, and legible — more like a playable geopolitical simulation than a loose chatbot demo.
