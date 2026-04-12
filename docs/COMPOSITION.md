# Skill Composition Guide

## The Composition Model

FLUX skills compose through JSON data. Every skill:
- Accepts JSON input (or reads CONFIG.yaml)
- Produces JSON output
- Can read other skills' output files

No special adapters. No protocol negotiation. Just files.

## Composition Patterns

### Chain (Linear)
```
murmur → spreader → dreamer
  Think     Analyze    Schedule
```

### Fan-Out (Parallel)
```
          ┌→ spreader
murmur →  ├→ dreamer
          └→ streamer
```

### Loop (Iterative)
```
murmur → spreader → murmur (deeper exploration of synthesis)
```

### Selector (Conditional)
```
murmur → confidence filter
         ├ high confidence → streamer (publish it)
         └ low confidence → murmur (think more)
```

## Composability by Skill

### murmur (Thinking)
- **Feeds into**: spreader, dreamer, streamer
- **Accepts from**: spreader synthesis, streamer high-ranked content
- **Output**: tensor.json with thoughts array

### spreader (Perspectives)
- **Feeds into**: murmur (for deeper exploration), dreamer (for scheduled expansion)
- **Accepts from**: murmur tensor output, any JSON with an "idea" field
- **Output**: spread.json with results array and synthesis

### dreamer (Scheduled Generation)
- **Feeds into**: streamer (best content becomes permanent), spreader (analyze generated content)
- **Accepts from**: murmur output as context, spreader synthesis as topic
- **Output**: generated content with metadata

### streamer (Autonomous Stream)
- **Feeds into**: murmur (deep analysis of popular content), spreader (multi-view of themes)
- **Accepts from**: any skill's output as seed content
- **Output**: ranked stream of content

## Example Compositions

### Deep Research Pipeline
```bash
# Think about a topic for 50 iterations
python3 runtime/skill_vm.py skills/murmur/skill.fluxbc

# Spread the best insights across 5 perspectives
python3 runtime/skill_vm.py skills/spreader/skill.fluxbc --input murmur-output/tensor.json

# Think deeper about the consensus points
python3 runtime/skill_vm.py skills/murmur/skill.fluxbc --input spreader-output/spread.json --config override.yaml
```

### Content Engine
```bash
# Generate content overnight
python3 runtime/skill_vm.py skills/dreamer/skill.fluxbc

# Analyze what was generated
python3 runtime/skill_vm.py skills/spreader/skill.fluxbc --input dreamer-output/latest.json

# Stream the best stuff
python3 runtime/skill_vm.py skills/streamer/skill.fluxbc --seed spreader-output/synthesis.json
```

## Building New Compositions

To compose skills that weren't designed for each other:

1. Read both AGENT.md files
2. Check INPUT/OUTPUT schemas for compatibility
3. If formats don't match, write a thin adapter (5-10 lines of Python)
4. Test with small data first
5. If it works well, submit the composition as an example to flux-skills

The composition doesn't need to be in the skills themselves — it's just how you invoke them.
