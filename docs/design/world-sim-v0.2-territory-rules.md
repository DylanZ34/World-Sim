# World Sim v0.2 - Territory Rules

## Overview

This document describes the territory expansion mechanics for World Sim v0.2, inspired by Civilization-style gameplay.

---

## 1. City Properties

Each city has the following properties:

| Property | Range | Description |
|----------|-------|-------------|
| `id` | string | Unique city identifier |
| `name` | string | City name |
| `x`, `y` | float | Map coordinates (0-1) |
| `population` | 0-10 | Citizens available for units |
| `fortification` | 0-10 | Defense strength |
| `size` | 0-10 | Max population capacity |
| `owner` | nation_id / null | City owner |
| `units` | array | Units stationed here |

### Starting Values

- **Capitals:** population 8, fortification 4, size 10
- **Regular cities:** population 4, fortification 2, size 6-8

---

## 2. Units

Units are stored in cities. Multiple units can occupy one city.

| Unit | Population Cost | Attack | Defense |
|-----|-----------------|--------|---------|
| militia | 1 | 1 | 1 |
| soldier | 2 | 2 | 2 |
| legion | 3 | 4 | 3 |
| cavalry | 3 | 3 | 2 |
| siege | 4 | 5 | 1 |

---

## 3. Action Types

### 3.1 Army Action (Expansion)

```json
{
  "type": "army",
  "source": "city_id",
  "target": "city_id",
  "unit": "legion",
  "count": 2,
  "mission": "conquer"
}
```

- **source:** Your city sending army (must own it)
- **target:** Target city (must be connected)
- **unit:** Unit type to send
- **count:** Number of units
- **mission:** "conquer", "raid", or "defend"

**Rules:**
- Must have enough population in source to create units
- Cannot move through enemy territory
- Target must be reachable by connected routes

### 3.2 Buy Action (Purchase Neutral City)

```json
{
  "type": "buy",
  "target": "city_id",
  "nation": "nation_1"
}
```

**Cost formula:**
```
base_cost = 2
discount = floor(nation_industry / 2)
final_cost = max(1, base_cost - discount)
```

| Nation Industry | Buy Cost |
|-----------------|---------|
| 0-1 | 2 |
| 2-3 | 1 |
| 4+ | 1 |

### 3.3 Fortify Action

```json
{
  "type": "fortify",
  "target": "city_id"
}
```

- +1 fortification to target city

---

## 4. Battle Resolution

### Attack Power
```
attack = (unit_attack × count) + √(source_population)
```

### Defense Power
```
defense = fortification + √(city_population) + home_bonus(2)
```

### Resolution Table

| Result | Winner Gets | Loser Gets |
|--------|-------------|-----------|
| Attack wins | Takes city | -50% population |
| Defense wins | City keeps | Attacker loses all units |
| Tie | Both retreat | -1 population both |

**Attacker always chooses when/where to attack (advantage)**

---

## 5. Population Growth

Growth occurs **per city, per turn**, only if:
- City has **no army stationed**
- Population < city size

| Food | Industry | Growth Rate |
|------|----------|------------|
| 7+ | 7+ | +1 per 20 turns (5%) |
| 5+ | 5+ | +1 per 50 turns (2%) |
| 3+ | 3+ | +1 per 100 turns (1%) |
| <3 | <3 | No growth |

---

## 6. Victory Conditions

- **All cities captured:** Nation eliminated from turn order
- **Last nation standing:** Controls all cities

---

## 7. Map Structure

The world map is stored in `world/map/world-map.json`:

```json
{
  "cities": {
    "city_0": {
      "id": "city_0",
      "name": "Hodges Capital",
      "x": 0.5,
      "y": 0.1,
      "owner": "nation_1",
      "population": 8,
      "fortification": 4,
      "size": 10,
      "units": []
    }
  },
  "connections": [["city_0", "city_1"], ...]
}
```

---

## 8. State Changes

### World State (extended)

```json
{
  "turn": 1,
  "nations": [
    {
      "id": "nation_1",
      "name": "Republic of Hodges",
      "treasury": 6,
      "force": 4,
      "food": 6,
      "stability": 7,
      "industry": 6,
      "relationships": {...}
    }
  ],
  "cityOwnership": {
    "city_0": "nation_1",
    "city_1": null
  },
  "cities": { /* city details */ },
  "connections": [...]
}
```

---

## 9. Turn Flow (with Territory)

1. Nations report army movements
2. Resolve all army movements (simultaneous)
3. Resolve battles
4. Apply population changes
5. Post turn summary

---

*Last updated: 2026-04-05*