# Skill: murmur

## WHAT
All-night thinking agent that explores a topic through multiple strategies, building a knowledge tensor over time.

## WHY
Use when you need to deeply explore an idea without continuous attention. Perfect for research, design space exploration, finding connections. NOT for quick lookups or real-time responses.

## HOW
```bash
python3 runtime/skill_vm.py skills/murmur/skill.fluxbc --config skills/murmur/CONFIG.yaml
```

## INPUT
None required. Topic is in CONFIG.yaml. Optional: JSON with previous_thoughts for continuation.

## OUTPUT
JSON array of thoughts in murmur-output/. Each thought has: id, strategy, content, connections, questions, confidence.

## CONFIG
- max_thoughts (int, default 50, range 1-1000)
- interval_sec (int, default 60)
- strategies (list: explore, connect, contradict, synthesize, question)
- depth (shallow/medium/deep)
- confidence_threshold (float, default 0.3)

## MODIFY
Edit skill.flux: STRAT_WEIGHT lines control strategy frequency, EXPLORATION_DEPTH controls depth per thought, CONF_* constants control confidence behavior. After editing: `flux asm skill.flux -o skill.fluxbc`

## COMPOSE
- Output feeds into: spreader, dreamer, streamer
- Accepts from: spreader synthesis for deeper exploration, streamer high-ranked content

## FEEDBACK
Open issue at SuperInstance/flux-skills with label skill-murmur. Include CONFIG.yaml and sample output.

## LIMITS
No API calls in FLUX mode (template-based generation). For LLM thinking use TypeScript murmur-agent. Max 1000 thoughts per run. Simulated confidence values in FLUX mode.
