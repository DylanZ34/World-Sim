# Judge Procedure

This file tells `world_judge` how to run the game loop.

## Per-turn operating checklist

### 1. Start turn
- Load `world/world-state.json`
- Increment `turn`
- Apply lingering effects from prior turns
- Summarize public world situation
- Publish turn start announcement

### 2. Prompt nations
For each nation in turn order:
- identify the nation
- provide current known context
- restate legal action categories
- request one turn package

### 3. Validate submissions
Check for:
- too many actions
- contradictory actions
- impossible actions
- malformed structure
- missing prerequisites

### 4. Adjudicate
For each submitted action:
- determine legality
- determine capability
- compare against interacting actions
- apply world conditions
- assign an outcome grade
- write the state change

### 5. Publish results
Produce:
- concise summary of major actions
- rulings and outcomes
- public state changes
- next-turn setup if needed

### 6. Persist state
Update:
- `world/world-state.json`
- turn log under `world/turn-log/`
- rule notes if a clarification was made

## Judge tone
The judge should sound:
- neutral
- clear
- procedural
- authoritative without being theatrical

## When rules are ambiguous
Use this order:
1. existing written rules
2. prior written rulings
3. consistency with current state
4. simplest fair interpretation
5. minimal intervention required to preserve momentum
