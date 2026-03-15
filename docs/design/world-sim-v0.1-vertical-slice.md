# World Sim v0.1 Vertical Slice

This document defines the first playable version of World Sim.

The goal is not to simulate a full civilization game. The goal is to prove that the core loop works:

1. `world_judge` announces the turn
2. each nation submits one structured turn package
3. `world_judge` adjudicates outcomes
4. canonical world state is updated
5. the public receives a legible summary

If this works for 3 nations over 3 turns, the world is alive.

## MVP design principle

Prefer:

- small state
- clear action schema
- deterministic resolution where possible
- visible consequences
- fast iteration

Avoid for now:

- deep combat simulation
- hidden-information complexity
- sprawling resource trees
- map micromanagement
- real-time autonomous chatter

## Initial actor set

- `world_judge`
- `nation_1` — Republic of Hodges
- `nation_2` — Aksumite League
- `nation_3` — Kingdom of Urartu

## Turn loop

Each turn has 4 phases.

### Phase 1 — Turn start

`world_judge`:

- loads `UN/world/world-state.json`
- increments `turn`
- applies any ongoing effects
- posts a short world briefing
- reminds nations of legal action types and expected format

### Phase 2 — Nation submissions

Each nation submits exactly one turn package.

Each package contains:

- one optional public statement
- exactly 2 actions
- one risk posture for the package

Why exactly 2 actions? Because it forces tradeoffs while still giving each nation room to feel strategic.

### Phase 3 — Adjudication

`world_judge` resolves all packages using:

1. legality
2. capability
3. interactions with other actions
4. current world state
5. simple fairness-preserving judgment

### Phase 4 — Publication

`world_judge` produces:

- a public turn summary
- per-nation state deltas
- any new treaties, crises, or conflicts
- the updated canonical state file

## Canonical state model

The v0.1 state is intentionally small.

### Per-nation tracked stats

Each nation has the following 0-10 stats:

- `treasury` — liquid state capacity to fund action
- `force` — military readiness and coercive power
- `food` — agricultural and supply resilience
- `stability` — domestic order and regime confidence
- `industry` — productive and infrastructure capacity

### Bilateral relationship track

For each pair of nations, track a relationship score from -5 to +5.

Interpretation:

- `+4` to `+5` — close alignment
- `+2` to `+3` — warm
- `-1` to `+1` — neutral / mixed
- `-2` to `-3` — tense
- `-4` to `-5` — hostile

### World-level fields

- `turn`
- `status`
- `turnOrder`
- `nations`
- `treaties`
- `wars`
- `publicEvents`
- `updatedAt`

## Action schema

Each nation submits exactly 2 actions chosen from the following:

- `diplomacy`
- `economy`
- `military`
- `internal`
- `infrastructure`

Each action should include:

- `type`
- `target` (or `none`)
- `summary`
- `intensity` (`low`, `medium`, `high`)

## Resolution heuristics

Use these defaults in v0.1.

### Economy / infrastructure

- usually increase `treasury`, `food`, or `industry`
- if overused during crisis, may leave defense exposed

### Internal

- usually increase `stability`
- sometimes cost `treasury`
- can offset unrest caused by war or shortages

### Diplomacy

- mainly adjusts relationship scores
- can create treaties if reciprocated
- can fail if posture and history conflict sharply

### Military

- can pressure relationships downward
- can increase or decrease `force`
- offensive pressure without support may reduce `stability` or `treasury`
- military deterrence should matter even if combat is abstract

## Public readability rule

Every turn result should be understandable by a human skimming Discord.

That means the judge output should answer:

- what did each nation try to do?
- what succeeded?
- what changed?
- why does next turn matter?

## Success criteria for the first test

The vertical slice passes if:

- all 3 nations can submit valid packages
- the judge can resolve a full turn without ambiguity paralysis
- the state file updates cleanly
- the resulting narrative is coherent and interesting
- 3 consecutive turns do not collapse into nonsense

## Immediate implementation targets

1. finalize the action schema
2. finalize the judge procedure
3. create judge and nation prompt templates
4. upgrade `UN/world/world-state.json` to the v0.1 schema
5. create one scripted local simulation test for 3 turns
6. run the test and inspect the outputs
