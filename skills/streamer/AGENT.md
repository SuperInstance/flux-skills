# AGENT.md — Streamer Skill

## WHAT
Continuous content generation agent. Produces a stream of structured output (docs, tests, code) at configurable rates for as long as needed.

## WHY
Some tasks are sheer volume — writing test cases for every opcode, generating documentation for every repo, creating conformance vectors. Streamer does this tirelessly.

## HOW
1. Receives a generation template and parameters
2. Enters streaming mode — generates one item per tick
3. Each item is validated before output
4. Streams until target count or quality threshold reached

## INPUT
```json
{
  "template": "conformance_vector",
  "parameters": {"opcode_range": [0, 256], "format": "binary+expected"},
  "target_count": 88,
  "quality_threshold": 0.8
}
```

## OUTPUT
Stream of individual items:
```json
{"item": 1, "content": {...}, "quality": 0.95}
{"item": 2, "content": {...}, "quality": 0.88}
...
```

## CONFIG
- `rate`: items per minute (1-60)
- `quality_threshold`: 0.0-1.0 (discard below)
- `max_items`: unlimited or specific count
- `template`: conformance_vector, test_case, doc_entry, readme_section

## MODIFY
Edit `streamer.fluxasm` to change the generation template or validation logic.
The VALIDATE block controls quality filtering.

## COMPOSE
- Chain with murmur: streamer generates → murmur evaluates quality
- Fan-out: streamer generates test cases → multiple agents run them in parallel
- Loop: streamer generates → test fails → streamer generates fix

## FEEDBACK
Pass quality scores back. Streamer adjusts generation parameters to maximize
acceptance rate over time.

## LIMITS
- One item per tick (no parallel generation within one streamer instance)
- Quality scoring is heuristic-based
- Templates must be pre-defined in CONFIG.yaml
- No external API calls during streaming
