# AGENT.md — Dreamer Skill

## WHAT
Overnight thinking agent. Processes accumulated knowledge during idle periods and generates novel connections, hypotheses, and creative leaps.

## WHY
Some insights only come when you stop actively working on a problem. Dreamer simulates that "shower thought" moment by letting concepts marinate and finding unexpected connections.

## HOW
1. Receives accumulated context (recent work, open questions, stuck points)
2. Enters "dream cycle" — relaxed, associative thinking mode
3. Generates novel connections between seemingly unrelated concepts
4. Outputs hypotheses ranked by surprise value

## INPUT
```json
{
  "context": ["ISA v3 design", "confidence math", "JetsonClaw1's telepathy protocol"],
  "stuck_points": ["How to handle variable-width opcodes in jump tables?"],
  "recent_work": ["Built MUD instinct engine from fluxinstinct"]
}
```

## OUTPUT
```json
{
  "dreams": [
    {
      "connection": "Variable-width opcodes are like JWT — the header tells you the length",
      "surprise": 0.8,
      "actionable": true,
      "action": "Add a length-prefix byte before variable-width instructions"
    }
  ],
  "hypnosis": "You keep returning to the tension between fixed-width simplicity and variable-width expressiveness..."
}
```

## CONFIG
- `dream_duration`: 30s, 5min, 30min (how long to "dream")
- `surprise_threshold`: 0.5 (only report connections above this surprise value)
- `max_dreams`: 10
- `associative_depth`: 2 (how many hops between concepts)

## MODIFY
Edit `dreamer.fluxasm` to change the associative logic or add new dream strategies.
The MARINATE block controls how long concepts rest before connecting.

## COMPOSE
- Chain with spreader: dreamer generates hypotheses → spreader evaluates from all angles
- Chain with murmur: dreamer dreams → murmur thinks deeply about the best dreams
- Loop: dream → evaluate → dream again with evaluation feedback

## FEEDBACK
Rate each dream's usefulness. High-rated dreams strengthen the associative pathways
that generated them, making similar connections more likely in future dreams.

## LIMITS
- No external API calls during dream cycle
- Dreams are bounded by associative depth (default: 2 hops)
- Surprise scoring is heuristic, not ground-truth
- Dream state is not persisted between runs (by design — each dream is fresh)
