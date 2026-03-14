# World Sim Discord Architecture

## Overview

This document defines the initial architecture for **World Sim**, a turn-based geopolitical simulation inspired by games like **Civilization**, with AI-controlled nations interacting through Discord.

The design adopts:

- **Option B**: multiple Discord bot accounts, one per in-world actor
- **Mechanism 3**: explicit trigger rules to control participation and avoid bot loops
- **Turn-based gameplay**: structured rounds mediated by a world authority agent

Initial actor set:

- `world_judge`
- `nation_1`
- `nation_2`
- `nation_3`

## Goals

- Simulate a small world of competing and cooperating nations
- Give each nation a distinct identity, incentives, and strategy
- Let all actors appear as separate participants inside the same Discord server
- Keep the simulation coherent, auditable, and resistant to runaway chatter
- Support incremental growth from 4 agents to a larger roster later

## Core Design Choice

### Why Option B

Each in-world actor gets its **own Discord bot account** and its **own OpenClaw agent**.

This gives us:

- separate names, avatars, and personalities in Discord
- clear identity boundaries between actors
- separate agent workspaces and memory/session stores
- a natural roleplay feel, since each nation visibly "speaks" as itself

This is better than a single bot routing to multiple internal agents when the primary product goal is to simulate a multi-party diplomatic world in one shared chat environment.

## Simulation Style

The game is **turn-by-turn**, not freeform real-time chatter.

The intended feel is similar to Civilization:

- the world advances in rounds/turns
- each nation evaluates the current state
- each nation submits actions or statements for the turn
- the judge resolves consequences
- the world state updates
- the next turn begins

This structure is critical for stability. It prevents all agents from speaking at once and makes state transitions explicit.

## Actor Model

### 1. `world_judge`

The `world_judge` is the referee and orchestrator.

Responsibilities:

- announces turn start and turn end
- publishes world events
- enforces game rules
- validates nation actions
- resolves conflicts and uncertainty
- updates canonical world state
- decides what information is public vs private
- triggers nation turns in the correct order
- prevents out-of-turn speaking when needed

The judge is **not** just another nation. It is the source of truth for the simulation timeline.

### 2. `nation_1`, `nation_2`, `nation_3`

Each nation agent represents a sovereign actor with its own:

- political identity
- objectives
- strategic doctrine
- public posture
- private constraints
- economic/military/diplomatic state
- memory of past interactions

Each nation should be opinionated and asymmetric. They should not collapse into generic diplomatic language.

## Discord Topology

## Shared public spaces

Recommended initial channels:

- `#world-news` — judge posts official turn updates, global events, rule decisions
- `#summit` — public diplomacy among nations
- `#rules-and-status` — pinned game rules, current turn number, score/state summaries

## Optional private spaces

Recommended optional private channels:

- `#nation-1-private`
- `#nation-2-private`
- `#nation-3-private`

These can be used later for:

- hidden plans
- private human intervention
- nation-specific reports
- secret diplomacy if the project evolves to support it

## Identity mapping

Each Discord bot account maps to one OpenClaw agent:

- `judgebot` -> `world_judge`
- `nation1bot` -> `nation_1`
- `nation2bot` -> `nation_2`
- `nation3bot` -> `nation_3`

## Triggering Model (Mechanism 3)

Mechanism 3 means agents do **not** freely respond to every message.

Instead, each bot speaks only when explicitly allowed by game rules.

### Trigger rules

A nation agent may respond only when one of the following is true:

1. it is directly mentioned
2. it is explicitly addressed by name/role
3. it is currently that nation's turn
4. `world_judge` has issued a prompt or turn instruction allowing it to act

The `world_judge` may respond when:

1. a human organizer requests a world action
2. a turn transition is needed
3. a rules adjudication is required
4. a nation action needs resolution

### Why this matters

This prevents:

- feedback loops between bots
- simultaneous uncontrolled replies
- noisy or incoherent diplomacy
- accidental exponential message storms

This mechanism is essential to making a multi-bot same-server simulation workable.

## Turn Structure

## High-level flow

Each turn proceeds in phases.

### Phase 0: Turn initialization

`world_judge`:

- increments the turn counter
- loads current world state
- applies scheduled effects
- posts any global event for the turn
- announces turn order

### Phase 1: Nation decision prompts

The judge prompts each nation in sequence.

Example:

1. `nation_1`, submit your turn
2. `nation_2`, submit your turn
3. `nation_3`, submit your turn

Prompts should include enough structured context for consistent play:

- current turn number
- public world summary
- any nation-specific visible facts
- legal action types
- deadline or expected output format

### Phase 2: Nation action submission

Each nation replies with one turn package, for example:

- diplomatic statement
- domestic policy choice
- military movement
- economic action
- research/infrastructure investment
- treaty proposal
- espionage attempt
- trade offer

A nation should ideally emit a structured action bundle plus optional flavor text.

### Phase 3: Adjudication

`world_judge`:

- validates legality of submitted actions
- resolves action interactions
- applies deterministic rules where possible
- applies probabilistic or judgment-based outcomes where needed
- publishes public results
- updates hidden/private state as needed

### Phase 4: End-of-turn publication

`world_judge` posts:

- summary of what happened this turn
- updated standings or status snapshot
- any wars, treaties, crises, discoveries, or disasters
- next-turn setup

## Turn order options

Initial recommendation:

- fixed order for MVP (`nation_1`, `nation_2`, `nation_3`)

Possible future upgrades:

- initiative-based order
- event-driven interrupt windows
- diplomacy phase + action phase separation
- simultaneous hidden orders resolved together

For the first version, fixed order is simpler and easier to debug.

## State Model

The simulation needs a **canonical world state** owned by `world_judge`.

### Canonical state

The judge maintains authoritative records for:

- turn number
- map/regions
- resources
- economy
- military forces
- technology/research
- diplomatic relationships
- treaties and alliances
- wars and disputes
- public events
- hidden events if supported

### Nation-local state

Each nation agent may maintain local working memory such as:

- strategic doctrine
- interpretation of rivals
- long-term goals
- negotiation history
- private plans

But nation-local state is **not authoritative**. If there is any conflict, `world_judge` wins.

## Suggested file layout

A good initial repository structure could look like this:

```text
World-Sim/
  docs/
    design/
      world-sim-discord-architecture.md
  config/
    openclaw.world-sim.json5
  world/
    world-state.json
    rules.md
    turn-log/
  agents/
    world_judge/
      AGENTS.md
      SOUL.md
      state/
    nation_1/
      AGENTS.md
      SOUL.md
      profile.md
      state/
    nation_2/
      AGENTS.md
      SOUL.md
      profile.md
      state/
    nation_3/
      AGENTS.md
      SOUL.md
      profile.md
      state/
```

## Agent workspace philosophy

Each agent should feel like a separate actor, not a parameterized copy.

### `world_judge` workspace should contain

- world rules
- adjudication principles
- event generation logic
- canonical state files
- turn management checklist
- allowed output formats

### nation workspace should contain

- nation identity and political philosophy
- strategic priorities
- resource profile
- strengths/weaknesses
- diplomatic style
- red lines
- long-term goals
- current situation notes

## OpenClaw configuration approach

We should configure Discord multi-account support, with one account per actor, and bind each account to its agent.

Conceptual config:

```json5
{
  agents: {
    list: [
      { id: "world_judge", workspace: "./agents/world_judge" },
      { id: "nation_1", workspace: "./agents/nation_1" },
      { id: "nation_2", workspace: "./agents/nation_2" },
      { id: "nation_3", workspace: "./agents/nation_3" }
    ]
  },

  channels: {
    discord: {
      defaultAccount: "judgebot",
      accounts: {
        judgebot: { token: "TOKEN_JUDGE" },
        nation1bot: { token: "TOKEN_N1" },
        nation2bot: { token: "TOKEN_N2" },
        nation3bot: { token: "TOKEN_N3" }
      },
      groupPolicy: "allowlist",
      guilds: {
        "YOUR_SERVER_ID": {
          requireMention: false
        }
      }
    }
  },

  bindings: [
    { match: { channel: "discord", accountId: "judgebot" }, agentId: "world_judge" },
    { match: { channel: "discord", accountId: "nation1bot" }, agentId: "nation_1" },
    { match: { channel: "discord", accountId: "nation2bot" }, agentId: "nation_2" },
    { match: { channel: "discord", accountId: "nation3bot" }, agentId: "nation_3" }
  ]
}
```

This is not the full final config, but it is the design baseline.

## Message discipline

To keep the simulation legible, agents should produce disciplined outputs.

### Judge output style

The judge should prefer:

- round announcements
- concise adjudications
- explicit rulings
- structured state updates
- clear next-action prompts

### Nation output style

Nation agents should prefer:

- one turn response per prompt
- strategic but in-character speech
- explicit declared actions
- concise diplomatic prose
- no repeated self-triggering chatter

## MVP scope

The first playable version should support:

- 1 judge
- 3 nations
- 1 shared Discord server
- 1 public summit channel
- turn-based action cycle
- simple world state persistence
- public diplomacy
- basic economic and military actions
- manual or semi-manual turn progression

## Non-goals for MVP

Not needed in version 1:

- real-time autonomous bot conversation
- dozens of nations
- complex hidden-information systems
- full map visualization
- sophisticated combat engine
- automatic long-running unsupervised loops

## Key risks

### 1. Bot loop risk

If mention rules or trigger discipline are too loose, bots may reply to each other indefinitely.

Mitigation:

- use explicit turn gating
- keep nation agents mostly silent outside prompt windows
- use judge-mediated progression

### 2. Personality collapse

Nation agents may drift into sounding too similar.

Mitigation:

- strong per-nation identity files
- asymmetric incentives
- different risk profiles and doctrines

### 3. State drift

Nation beliefs may diverge from authoritative state.

Mitigation:

- judge owns canonical world state
- judge summaries are treated as truth
- nation prompts include refreshed state context

### 4. Over-complexity too early

It is easy to overdesign diplomacy, economy, and military mechanics.

Mitigation:

- keep rules minimal at MVP
- prefer simple action types
- add complexity only after stable playtests

## Recommended next steps

1. Create the four agent workspaces under `agents/`
2. Write identity and behavior docs for `world_judge` and each nation
3. Draft a first-pass ruleset for turn order and legal actions
4. Create the OpenClaw multi-account Discord config file
5. Define the nation turn-response schema
6. Define the judge adjudication/update schema
7. Run a tiny 3-turn simulation in a test Discord server

## Initial recommendation summary

The World Sim MVP should be built as a **multi-bot, multi-agent, turn-based Discord simulation**.

The architecture should use:

- **one Discord bot account per actor**
- **one OpenClaw agent per actor**
- **judge-mediated turns**
- **explicit trigger rules**
- **canonical world state under `world_judge`**

This gives the project the strongest balance of:

- clarity
- roleplay quality
- engineering control
- extensibility
- protection against chaotic bot interactions
