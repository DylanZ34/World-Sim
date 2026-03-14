# World Sim Rules v0.1

This is the first playable ruleset for the World Sim.

The **world_judge** runs these rules, interprets them, and maintains the canonical world state.

## 1. Governing principles

1. **The judge is the source of truth.**
   - The judge owns canonical state.
   - Nation beliefs, claims, or rhetoric are not authoritative.
2. **The world advances in turns.**
   - No free-form autonomous chatter as core gameplay.
   - Major game actions happen only during valid turn windows.
3. **One package per nation per turn.**
   - Each nation submits a single turn package when prompted.
4. **Public results, private intent only when supported.**
   - MVP defaults to legible public outcomes.
5. **Rulings should preserve fairness, clarity, and momentum.**
   - When rules are incomplete, the judge makes the narrowest ruling that keeps play moving.

## 2. Actors

### 2.1 World Judge

The judge:
- starts and closes turns
- prompts nations in order
- validates actions
- resolves conflicts
- updates state
- publishes results
- records rule clarifications

### 2.2 Nations

Each nation is a sovereign actor with:
- identity
- goals
- capabilities
- relationships
- internal strategy

A nation may act only when:
- it is explicitly prompted by the judge
- it is directly addressed under an allowed diplomacy window
- a rule explicitly permits its response

## 3. Turn structure

Each turn has 4 phases.

### Phase 0 — Turn initialization
The judge:
- increments the turn counter
- loads canonical state
- applies ongoing effects
- announces the world situation
- states turn order

### Phase 1 — Nation prompts
The judge prompts each nation in sequence.

Each prompt should include:
- current turn number
- public world summary
- that nation's known situation
- legal action categories
- required output shape

### Phase 2 — Nation submissions
Each nation submits one turn package containing:
- optional public statement
- 1 to 3 declared actions
- optional rationale/flavor

### Phase 3 — Adjudication and publication
The judge:
- checks legality
- resolves interactions
- applies outcomes
- updates canonical state
- publishes a turn summary

## 4. Legal action categories

For MVP, a nation may choose up to **3 actions** per turn from these categories.

### 4.1 Diplomacy
Examples:
- issue public statement
- offer treaty
- propose alliance
- threaten sanctions
- recognize another state
- open negotiations

### 4.2 Economy
Examples:
- invest in industry
- expand agriculture
- build infrastructure
- redirect budget
- pursue trade deal

### 4.3 Military
Examples:
- recruit forces
- fortify region
- reposition forces
- patrol border
- launch limited attack
- declare war

### 4.4 Research / development
Examples:
- invest in science
- pursue doctrine upgrade
- improve logistics
- develop resource extraction

### 4.5 Internal policy
Examples:
- stabilize unrest
- centralize power
- reform administration
- raise taxes
- subsidize key sectors

## 5. Action constraints

1. A nation may submit at most **3 actions** per turn.
2. Duplicate or contradictory actions in the same turn may be rejected or reduced.
3. Actions requiring prerequisites fail if the prerequisites are absent.
4. Actions may create tradeoffs in economy, stability, military readiness, or diplomacy.
5. Major wars, alliances, or territorial changes must be recorded explicitly by the judge.

## 6. Resolution rules

When actions interact, the judge resolves them using this priority order:

1. **Legality** — is the action allowed?
2. **Capability** — does the nation have the means?
3. **Conflict interaction** — what happens when actions collide?
4. **World conditions** — terrain, scarcity, unrest, current wars, treaties
5. **Outcome scaling** — success, partial success, stalemate, failure, backlash

### 6.1 Outcome grades
The judge may assign one of these result classes:
- Success
- Partial Success
- Stalemate
- Failure
- Success with Cost
- Failure with Consequence

### 6.2 Tie-break philosophy
When resolution is uncertain, prefer:
- consistency with prior rulings
- the simpler interpretation
- outcomes that keep future play interesting
- outcomes that do not arbitrarily destroy an actor without setup

## 7. War and conflict

For MVP:
- war is allowed
- instant total conquest is not
- military actions should produce incremental consequences
- border clashes and limited offensives are easier to justify than total collapse

The judge should resolve war through:
- force balance
- readiness
- logistics
- diplomatic context
- previous positioning
- surprise or defensive advantage when justified

## 8. Diplomacy rules

- Nations may make public offers and threats.
- Treaties only become active when all required parties clearly accept.
- The judge records whether a treaty is proposed, active, violated, or dissolved.
- Public rhetoric alone does not change canonical relations unless the judge records it as a state change.

## 9. Economy and development rules

The judge tracks broad abstractions, not detailed spreadsheets.

Recommended MVP stats per nation:
- economy
- military
- stability
- technology
- diplomatic posture
- key resources

Economy actions may improve future capacity but often have delayed payoff.
Military expansion should usually impose economic or stability costs.

## 10. Public vs canonical truth

- Public statements are in-world speech.
- Canonical truth is the judge's recorded state.
- Nations may bluff, boast, or mislead.
- The judge must not confuse rhetoric with fact.

## 11. Invalid submissions

If a nation submits an invalid turn package, the judge may:
- reject it and request a corrected package
- partially accept the valid portions
- convert it into a weaker fallback action

If a nation fails to act, the judge may assign a default passive turn such as:
- hold position
- maintain status quo
- minor internal management

## 12. State changes the judge must record

At minimum, after each turn the judge updates:
- turn number
- nation stats
- diplomatic relationships
- wars / treaties
- territorial control if relevant
- major public events
- unresolved crises

## 13. Rule change policy

If the rules need to change:
- the judge should document the change
- the change should take effect clearly from a named turn onward
- retroactive changes should be avoided unless they correct a clear error

## 14. MVP default design stance

When the rules do not specify detail, the judge should prefer:
- simple abstractions over simulation bloat
- legibility over hidden complexity
- strategic differentiation over mechanical noise
- consistent rulings over clever improvisation
