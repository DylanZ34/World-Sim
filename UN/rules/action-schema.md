# Nation Turn Package Schema v0.2

Each nation submits exactly one package per turn.

The package should be easy for both a judge agent and a human reader to parse.

## JSON shape (v0.2 with territory)

```json
{
  "turn": 1,
  "nation": "nation_1",
  "risk": "medium",
  "public_message": "The Republic of Hodges expands eastward.",
  "actions": [
    {
      "type": "army",
      "source": "city_0",
      "target": "city_3",
      "unit": "legion",
      "count": 2,
      "mission": "conquer"
    },
    {
      "type": "buy",
      "target": "city_2",
      "nation": "nation_1"
    }
  ]
}
```

## Required rules

- `turn` must match the active world turn
- `nation` must match the acting nation
- `risk` must be one of: `low`, `medium`, `high`
- `actions` must contain exactly 2 items in v0.2
- each action must include all required fields for its type
- action count must be exactly 2

## Action Types

### army (v0.2)
```json
{
  "type": "army",
  "source": "city_id",  // Your city
  "target": "city_id",  // Target city
  "unit": "legion",     // militia, soldier, legion, cavalry, siege
  "count": 1,           // Number of units
  "mission": "conquer"   // conquer, raid, defend
}
```

### buy (v0.2)
```json
{
  "type": "buy",
  "target": "city_id",
  "nation": "nation_1"  // Your nation ID
}
```

### fortify (v0.2)
```json
{
  "type": "fortify",
  "target": "city_id"
}
```

### economy, infrastructure, internal, diplomacy, military
Same as v0.1.

## Invalid examples

### Not enough population
```json
{
  "type": "army",
  "source": "city_0",
  "target": "city_1",
  "unit": "legion",
  "count": 10  // Exceeds population
}
```

### Target not connected
```json
{
  "type": "army",
  "source": "city_0",
  "target": "city_9",  // Not connected to source
  "unit": "soldier",
  "count": 1
}
```

## Cost Reference

| Unit | Population Cost |
|------|-----------------|
| militia | 1 |
| soldier | 2 |
| legion | 3 |
| cavalry | 3 |
| siege | 4 |

| Buy Cost | Nation Industry |
|----------|-----------------|
| 2 | 0-1 |
| 1 | 2-3 |
| 1 | 4+ |
