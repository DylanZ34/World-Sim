# Nation Agendas v0.2

## Concept

Each nation has a **victory agenda** - their ultimate goal that defines how they play and what they aim for. Agendas are randomized on world reset but fit each nation's character.

## Agenda Types

| Agenda | Description | PreferredStats | Win Condition |
|--------|-------------|-----------------|--------------|
| `world_conquest` | Dominate all cities | Force, Stability | Control 80%+ cities |
| `population_boom` | Grow the largest population | Food, Stability | 50+ total population |
| `trade_empire` | Accumulate maximum wealth | Treasury, Industry | 50+ treasury |
| `cultural_dominance` | Spread influence peacefully | Stability, Population | 3+ nations positively aligned |
| `military_might` | Build unstoppable army | Force, Industry | 30+ army units |
| `diplomatic_victory` | Win through alliances | Diplomacy | Treaties with all nations |

## Nation-Specific Agendas

### Republic of Hodges
**Character:** Civic-minded, lawful, trade-oriented

**Available agendas:**
- `civic_prosperity` - Build the happiest, most populated nation
- `trade_empire` - Dominate through commerce
- `diplomatic_victory` - Win through alliances

### Aksumite League  
**Character:** Merchant traders, profit-seeking

**Available agendas:**
- `trade_empire` - Maximum wealth accumulation
- `population_boom` - Grow merchant cities
- `cultural_dominance` - Spread trade influence

### Kingdom of Urartu
**Character:** Fortress-builders, defensive, strong military

**Available agendas:**
- `military_might` - Unstoppable army
- `world_conquest` - Total domination
- `defensive_empire` - Impenetrable defenses (high fortification on all cities)

## Agenda Assignment (on reset)

Each nation gets one random agenda from their pool:
- 40% primary agenda (their "ideal")
- 30% secondary 
- 30% alternative

## Display

Nations display their agenda in public:
- In #summit as their "national motto"
- In turn packages as context

## Example Turn Package with Agenda

```json
{
  "turn": 1,
  "nation": "nation_1",
  "agenda": "trade_empire",
  "public_message": "The Republic seeks prosperity through lawful commerce.",
  "actions": [...]
}
```

## Win Conditions

Each turn, judge checks:

| Agenda | Condition | Check |
|--------|-----------|-------|
| world_conquest | cities_with_owner >= 0.8 * total_cities | Every 10 turns |
| population_boom | sum(population for owned cities) >= 50 | Every turn |
| trade_empire | nation.treasury >= 50 | Every turn |
| cultural_dominance | allRelationships >= 3 | Every 10 turns |
| military_might | total_units >= 30 | Every turn |
| diplomatic_victory | treaties.length == 2 | Every 10 turns |

---

*Last updated: 2026-04-05*