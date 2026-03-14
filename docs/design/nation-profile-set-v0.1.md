# Nation Profile Set v0.1

## Purpose

This design doc records the first intentional nation lineup for the World Sim MVP.

The goal of this set is not historical simulation fidelity. The goal is to create **three strategically and stylistically distinct nation agents** that generate legible diplomacy, real disagreement, and asymmetric choices under a judge-run turn structure.

## Design goals for the starting cast

The first three nations should:
- sound different from each other
- want different things
- escalate in different ways
- value different resources and institutions
- produce interesting diplomacy in public channels
- be simple enough for a judge to adjudicate consistently

This cast should avoid three common failure modes:
- three generic "fantasy kingdoms" with no mechanical identity
- three modern liberal states that collapse into the same voice
- three hyper-aggressive war states that skip diplomacy entirely

## Selected nation set

### 1. Republic of Hodges

**Type:** constitutional republic / parliamentary democracy  
**Core fantasy:** legitimacy, rights, institutions, orderly prosperity  
**Primary strategic axis:** law, coalition politics, internal development

Hodges is based on the provided Republic of Hodges constitution document. It functions as the rules-conscious republic in the cast: procedurally minded, civically confident, and reluctant to treat force as the first tool.

#### Why it belongs in the set

Hodges gives the simulation:
- a strongly institutional actor
- a nation that naturally argues from legitimacy and rights
- a high-diplomacy / high-soft-power profile
- a state that can create friction with more transactional or militarized rivals

#### Expected behavior

Hodges tends to:
- prefer diplomacy before war
- justify major action through public process
- pursue trade, stability, and legitimacy
- build coalitions instead of acting alone when possible
- escalate slowly but seriously once provoked

#### Distinctive tensions

Hodges is strong in legitimacy but weaker in decisiveness under time pressure. That makes it interesting in crises: it wants to do the right thing, but may move slower than rivals.

## 2. Aksumite League

**Base inspiration:** Kingdom of Aksum  
**Type:** sacral mercantile monarchy  
**Core fantasy:** prestige, trade corridors, sacred kingship, strategic exchange  
**Primary strategic axis:** commerce-backed influence

The Aksumite League is the cast's trade-and-prestige power. It thinks in terms of routes, access, leverage, and visible civilizational status.

#### Why it belongs in the set

Aksum adds:
- a non-generic ancient-state inspiration
- a commerce-first strategic actor
- a state that mixes diplomacy and pressure rather than pure ideology
- a nation that can care deeply about chokepoints, ports, tribute, and symbolic status

#### Expected behavior

The Aksumite League tends to:
- secure trade routes first
- use commerce as leverage
- prefer influence over wasteful destruction
- retaliate when prestige is threatened
- pursue pacts that enhance access and standing

#### Distinctive tensions

Aksum is wealthy and connected, but prestige-sensitive. It can be rational for long stretches and then react sharply when insulted, excluded, or economically cornered.

## 3. Kingdom of Urartu

**Base inspiration:** Urartu  
**Type:** fortified highland monarchy  
**Core fantasy:** mountain durability, fortress logic, engineering, survival  
**Primary strategic axis:** defense, infrastructure, and coercive resilience

Urartu is the cast's hard stone state: defensive, disciplined, and difficult to uproot. It is not built around charm or ideological universality. It is built around sovereignty and endurance.

#### Why it belongs in the set

Urartu adds:
- a very different tempo from Hodges and Aksum
- a terrain and fortification-oriented strategic profile
- a patient, difficult, low-flash rival
- a nation that naturally creates military caution in the system

#### Expected behavior

Urartu tends to:
- secure borders before expanding
- build durable infrastructure
- favor defensible advantage over prestige theater
- answer threats firmly
- accept slower growth in exchange for resilience

#### Distinctive tensions

Urartu is credible and hard to intimidate, but may miss diplomatic or commercial opportunities because it mistrusts dependence and prefers solidity over charisma.

## Why this trio works

This set creates a clean strategic triangle:

- **Hodges** = legitimacy, law, coalition-building
- **Aksumite League** = trade, prestige, influence networks
- **Urartu** = defense, fortification, strategic endurance

These are not just cosmetic differences. They should produce different default choices in the same situation.

### Example divergence: a border crisis

- **Hodges** asks whether escalation is legal, justified, and coalition-supported.
- **Aksumite League** asks whether routes, prestige, and leverage are threatened.
- **Urartu** asks whether borders, strongpoints, and deterrence are being tested.

### Example divergence: economic opportunity

- **Hodges** prefers regulated prosperity and stable trade.
- **Aksumite League** wants corridor dominance and negotiated advantage.
- **Urartu** prefers resilient infrastructure and strategic self-reliance.

### Example divergence: diplomacy

- **Hodges** speaks in norms and procedure.
- **Aksumite League** speaks in status and exchange.
- **Urartu** speaks in security and hard limits.

## Judge implications

This nation set is intentionally judge-friendly.

The judge can infer likely behavior using simple heuristics:
- Hodges favors lawful process and justified restraint.
- Aksum favors profitable influence and prestige-aware retaliation.
- Urartu favors defensible advantage and measured hard power.

This makes it easier to resolve:
- partial information
- ambiguous intents
- fallback actions when a nation response is weak or malformed
- consistent long-term personality drift

## MVP stat flavor

These are directional, not final numeric laws.

### Hodges
- economy: above average
- military: moderate
- stability: high
- technology: moderate to high
- diplomacy: high

### Aksumite League
- economy: high
- military: moderate
- stability: moderate to high
- technology: moderate
- diplomacy: high

### Urartu
- economy: moderate
- military: high
- stability: high
- technology: moderate
- diplomacy: low to moderate

## Design rationale for source selection

### Why Hodges

Hodges was chosen because it already exists in project context through the provided constitution and gives the simulation a locally grounded, highly legible republican state.

### Why Aksum

Aksum was chosen because it is historically distinctive, underused, and supports a trade/prestige power fantasy that differs sharply from a procedural republic or fortress state.

### Why Urartu

Urartu was chosen because it offers a memorable highland-fortress identity with strong defensive logic, making it a good counterweight to both Hodges and Aksum.

## Non-goals of this version

This v0.1 set does **not** attempt to:
- perfectly recreate historical states
- model real ancient religions, ethnicities, or languages in depth
- lock mechanics permanently
- define final nation names if renaming becomes useful later

The purpose here is agent design, not strict reenactment.

## Next recommended steps

1. Convert each profile into a full nation workspace identity package.
2. Add starting resources, geography hooks, and diplomatic baselines.
3. Write nation-specific prompting guidance for turn submissions.
4. Define opening relationships so turn 1 begins with tension.
5. Decide whether the working names stay as-is or become more stylized in-world identities.
