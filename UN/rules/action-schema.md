# Nation Turn Package Schema

Each nation should submit one package per turn using this logical structure.

```json
{
  "turn": 1,
  "nation": "nation_1",
  "public_message": "Optional in-character statement",
  "actions": [
    {
      "type": "diplomacy",
      "summary": "Offer trade pact to nation_2"
    },
    {
      "type": "economy",
      "summary": "Invest in port infrastructure"
    }
  ]
}
```

## Rules

- `turn` must match the active turn
- `nation` must match the acting nation
- `actions` must contain 1 to 3 items
- each action should be short, concrete, and legible
- flavor text is welcome, but the action intent must be explicit

## Allowed action types

- `diplomacy`
- `economy`
- `military`
- `research`
- `internal`
