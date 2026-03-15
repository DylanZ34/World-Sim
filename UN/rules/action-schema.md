# Nation Turn Package Schema v0.1

Each nation submits exactly one package per turn.

The package should be easy for both a judge agent and a human reader to parse.

## JSON shape

```json
{
  "turn": 1,
  "nation": "nation_1",
  "risk": "medium",
  "public_message": "The Republic of Hodges calls for orderly trade and mutual restraint.",
  "actions": [
    {
      "type": "diplomacy",
      "target": "nation_2",
      "summary": "Offer a limited trade and non-aggression framework.",
      "intensity": "medium"
    },
    {
      "type": "infrastructure",
      "target": "none",
      "summary": "Expand domestic port and customs capacity.",
      "intensity": "medium"
    }
  ]
}
```

## Required rules

- `turn` must match the active world turn
- `nation` must match the acting nation
- `risk` must be one of: `low`, `medium`, `high`
- `actions` must contain exactly 2 items in v0.1
- each action must include `type`, `target`, `summary`, and `intensity`
- `intensity` must be one of: `low`, `medium`, `high`
- `target` should be another nation id or `none`
- action summaries must be concrete and operational, not vague slogans

## Allowed action types

- `diplomacy`
- `economy`
- `military`
- `internal`
- `infrastructure`

## Guidance by action type

### `diplomacy`
Use for:
- treaty offers
- trade deals
- recognition statements
- warnings
- alliance exploration
- public de-escalation

### `economy`
Use for:
- tax changes
- trade expansion
- industrial investment
- market or treasury measures
- resource extraction policy

### `military`
Use for:
- mobilization
- deterrence
- patrols
- border reinforcement
- punitive expedition
- exercises or shows of force

### `internal`
Use for:
- reforms
- public order measures
- legitimacy campaigns
- relief spending
- anti-corruption drives
- elite balancing

### `infrastructure`
Use for:
- roads
- ports
- irrigation
- forts
- depots
- logistics and productive capacity improvements

## Invalid examples

### Too vague

```json
{
  "type": "economy",
  "target": "none",
  "summary": "Improve the country",
  "intensity": "medium"
}
```

### Missing target

```json
{
  "type": "diplomacy",
  "summary": "Talk to nation_2",
  "intensity": "low"
}
```

### Wrong action count

A package with 1 or 3+ actions is invalid in v0.1.

## Judge handling of malformed packages

If a package is malformed, the judge should:

1. salvage intent if possible
2. downgrade effectiveness if clarity is poor
3. avoid blocking the whole turn unless the package is unusable

Momentum matters more than bureaucratic perfection.
