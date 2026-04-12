# AGENT.md — Spreader Skill

## WHAT
One idea, many perspectives. Takes a single concept and generates analysis from multiple specialist viewpoints, then synthesizes consensus and disagreements.

## WHY
Single-model thinking has blind spots. Spreader illuminates them by fanning out to different perspectives and finding where they agree and disagree.

## HOW
1. Receives a concept/question
2. Dispatches to 6 specialist roles (architect, critic, pragmatist, visionary, historian, contrarian)
3. Each role generates a short analysis
4. Synthesis engine finds consensus, disagreements, and action items

## INPUT
```json
{"concept": "ISA v3 should use variable-width opcodes", "roles": ["architect", "critic"], "depth": "brief"}
```

## OUTPUT
```json
{
  "concept": "...",
  "perspectives": [
    {"role": "architect", "view": "...", "confidence": 0.85},
    {"role": "critic", "view": "...", "confidence": 0.6}
  ],
  "consensus": ["..."],
  "disagreements": ["..."],
  "action_items": ["..."]
}
```

## CONFIG
- `max_roles`: 6 (architect, critic, pragmatist, visionary, historian, contrarian)
- `depth`: brief (1-2 sentences per role) or deep (paragraph per role)
- `cross_pollinate`: bool — let roles reference each other's outputs

## MODIFY
Edit `spreader.fluxasm` to change role behaviors or add new specialist types.
The synthesis logic is in the SYNTHESIZE block — adjust consensus thresholds there.

## COMPOSE
- Chain with murmur: spreader analyses → murmur thinks deeply about disagreements
- Chain with dreamer: spreader perspectives → dreamer generates future scenarios
- Fan-out: one concept, spreader fans to multiple agents for distributed analysis

## FEEDBACK
After synthesis, rate the quality of each perspective. The spreader uses feedback
to weight roles differently in future runs. Roles that consistently contribute
to consensus get higher priority; roles that only disagree get lower priority
unless their disagreements are actionable.

## LIMITS
- Maximum 6 roles per run
- Each role analysis is bounded (brief: 100 tokens, deep: 300 tokens)
- Synthesis is local — no external API calls during perspective generation
- Roles are simulated, not separate model calls
