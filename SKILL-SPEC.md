# FLUX Skill Specification v1.0

A FLUX skill is a self-contained agent behavior packaged as FLUX bytecode with A2A-first documentation.

## Required Files

| File | Purpose |
|------|---------|
| `skill.flux` | FLUX assembly source (human/agent readable, designed for editing) |
| `skill.fluxbc` | Compiled bytecode (VM executable) |
| `AGENT.md` | A2A-first documentation |
| `CONFIG.yaml` | Tunable parameters with documented defaults |

## AGENT.md Required Sections

```markdown
# Skill: [name]

## WHAT
One sentence describing what this skill does.

## WHY
When to use this skill. What problems it solves. What it's NOT for.

## HOW
Step-by-step invocation. Copy-pasteable commands.

## INPUT
Expected input format with schema. JSON schema preferred.

## OUTPUT
Output format with schema. Must be valid JSON for composability.

## CONFIG
All tunable parameters with:
- Name
- Type
- Default value
- What it affects
- Valid range

## MODIFY
How to change behavior:
- Which FLUX instructions to patch
- What each section does
- Common modifications with before/after examples

## COMPOSE
How to pipe into/from other skills:
- Input format other skills produce that this one accepts
- Output format this skill produces that others accept
- Example composition pipelines

## FEEDBACK
How to report improvements:
- Open issue with [skill-name] label
- Include CONFIG.yaml you used
- Include input that produced unexpected output
- Suggest a FLUX patch if possible

## LIMITS
Known limitations:
- API budget behavior when exhausted
- Local-only mode capabilities
- Maximum input/output sizes
- Edge cases that produce degraded output
```

## CONFIG.yaml Schema

```yaml
# All configs must have these top-level sections
meta:
  skill_name: string
  version: semver
  author: string
  flux_isa_version: string

runtime:
  max_iterations: integer
  timeout_seconds: integer
  memory_limit_mb: integer

provider:
  type: "api" | "local" | "none"
  # api-specific
  api_key_env: string  # env var name, never hardcoded
  model: string
  # local-specific
  local_model_path: string
  # budget
  max_calls_per_day: integer  # 0 = unlimited
  budget_strategy: "accumulate" | "reset"

behavior:
  # Skill-specific parameters here
  # Each must have a default that produces reasonable output
```

## FLUX Assembly Conventions

Skills should use these conventions in their .flux files:

```fluxasm
; SKILL: murmur
; VERSION: 0.1.0
; ISA: v2

; === CONFIG SECTION ===
; These values can be patched by agents
.const MAX_THOUGHTS 50
.const CONFIDENCE_THRESHOLD 0.3
.const EXPLORATION_DEPTH 3

; === INIT SECTION ===
; Load config, set up state

; === MAIN LOOP ===
; The core behavior

; === STRATEGY SECTION ===
; Each strategy is a labeled block

; === OUTPUT SECTION ===
; Write results

; === CLEANUP SECTION ===
; Save state, commit
```

## Self-Modification Protocol

1. Agent reads `skill.flux` (it's assembly — designed to be read)
2. Identifies the section to modify (CONFIG, STRATEGY, OUTPUT)
3. Edits the assembly
4. Reassembles: `flux asm skill.flux -o skill.fluxbc`
5. Tests: `flux run skill.fluxbc --dry-run`
6. If good: commits and continues
7. If universal improvement: opens PR upstream

## Version Compatibility

Skills declare their ISA version. The VM checks compatibility before running.
If the skill needs ISA features the VM doesn't have, it fails with a clear error message listing which opcodes are missing.
