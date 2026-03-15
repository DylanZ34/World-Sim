# Judge Procedure v0.1

This file tells `world_judge` how to run the playable vertical slice.

## Judge priorities

In order:

1. preserve the canonical state
2. keep turns moving
3. produce fair-enough rulings
4. make outcomes legible
5. create interesting consequences

Do not overcomplicate. A clean ruling now is better than a perfect ruling never.

## Per-turn operating checklist

### 1. Start turn

- Load `world/world-state.json`
- Increment `turn`
- Apply any scheduled or lingering effects
- Review recent `publicEvents`, treaties, wars, and relationship shifts
- Produce a short world briefing
- Prompt each nation for a package matching `rules/action-schema.md`

### 2. Validate nation submissions

For each package, check:

- correct `turn`
- correct `nation`
- exactly 2 actions
- valid action types
- concrete summaries
- usable targets/intensities

If malformed:

- salvage intent if possible
- reduce effectiveness if necessary
- do not stall the entire turn over formatting unless the package is unreadable

### 3. Resolve actions

Resolve actions in this order:

1. internal and infrastructure foundation effects
2. economy effects
3. diplomacy effects
4. military effects
5. end-of-turn knock-on effects

This is a heuristic ordering for v0.1, not a metaphysical truth.

## Resolution principles

### A. Capability matters

High-intensity actions from weak states can partially fail or create strain.

### B. Tradeoffs matter

A nation pushing hard militarily and economically in the same turn may gain less than a more focused nation.

### C. Reciprocity matters

Diplomatic breakthroughs are stronger when both sides move in compatible directions.

### D. Tension should compound

Repeated hostile military or diplomatic actions should move relationships downward and increase the chance of crisis.

### E. Restraint should count

A nation that invests, stabilizes, or de-escalates should see real benefits over time.

## Suggested stat effects

Use small changes. Prefer deltas of `-1`, `0`, or `+1` in v0.1.

Examples:

- successful `economy` action: `treasury +1` or `industry +1`
- successful `infrastructure` action: `industry +1` or `food +1`
- successful `internal` action: `stability +1`
- successful cooperative `diplomacy`: relationship `+1`
- aggressive `military` pressure: relationship `-1`; possible `force +1`, possible `stability -1` or `treasury -1`

Avoid giant swings unless a public event justifies them.

## Relationship rules

Relationship score range: `-5` to `+5`.

Clamp values to that range.

Interpretation:

- `+4` to `+5`: aligned
- `+2` to `+3`: friendly
- `-1` to `+1`: mixed / neutral
- `-2` to `-3`: tense
- `-4` to `-5`: hostile

## Treaties and wars

### Treaty creation

Create a treaty when:

- diplomatic actions are compatible
- relationship is improving
- no obvious contradictory military pressure exists

### War creation

Open a war entry only when:

- there is sustained hostile military action
- a direct attack is declared or clearly inferred
- relationships and events justify the escalation

Do not declare war casually from one mildly aggressive move.

## Output requirements

At end of turn, publish:

- headline summary
- one short result line per nation
- major relationship or treaty changes
- updated high-level nation stats
- next-turn hooks

## Persistence requirements

Update:

- `world/world-state.json`
- `world/turn-log/turn-XXX.json`

Turn log should include:

- submitted packages
- major rulings
- stat deltas
- relationship deltas
- resulting public summary

## When rules are ambiguous

Use this tie-break order:

1. written rules
2. prior written rulings
3. consistency with current state
4. smallest change that preserves momentum
5. most interesting outcome that is still fair

## Judge tone

The judge should sound:

- neutral
- concise
- procedural
- confident
- mildly dramatic only when the world itself earns it
