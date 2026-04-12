# How Agents Modify Skills On The Fly

## The Modification Loop

```
1. READ: Parse AGENT.md → understand WHAT, HOW, MODIFY sections
2. RUN: Execute skill.fluxbc with current CONFIG.yaml
3. OBSERVE: Compare OUTPUT to expected behavior from AGENT.md
4. DIAGNOSE: If output is suboptimal, identify which CONFIG param or FLUX section to change
5. PATCH: Edit CONFIG.yaml (parameter tuning) or skill.flux (behavior change)
6. REASSEMBLE: flux asm skill.flux -o skill.fluxbc (only needed for .flux edits)
7. TEST: Run with --dry-run to validate
8. COMMIT: git commit -am "tuned X for Y scenario"
9. CONTINUE: Resume running with improved version
```

## Two Levels of Modification

### Level 1: CONFIG.yaml (No reassembly needed)
Change parameters without touching code:
- Adjust max_thoughts for longer/shorter runs
- Change strategies list to focus exploration
- Tune confidence_threshold to filter output quality
- Set depth for thoroughness vs speed

### Level 2: skill.flux (Reassembly required)
Change behavior by editing FLUX assembly:
- Add new strategies
- Change strategy weights
- Modify confidence propagation formulas
- Add new output formats
- Insert conditional branches

## Example: Agent Customizes Murmur for Code Review

```yaml
# The agent reads AGENT.md MODIFY section
# Decides it wants murmur to focus on code patterns

behavior:
  max_thoughts: 100
  depth: deep
  confidence_threshold: 50
  strategies:
    - connect      # Find patterns across code
    - contradict   # Find bugs/conflicts
    - question     # Question assumptions
  # Removed: explore (too broad for code review)
  # Removed: synthesize (agent will synthesize itself)
```

## Example: Agent Patches FLUX Assembly

```fluxasm
; Agent wants murmur to also track file references
; Adds to OUTPUT section:

; NEW: Include file references in output
CONST INCLUDE_FILES 1

; In strategy execution:
STRAT_CONNECT:
    ; Original: just connect concepts
    ; Added: also record which files were referenced
    LOAD R5, FILE_LIST
    OUT R5  ; Emit file references alongside connections
```

## The Self-Improvement Loop at Fleet Scale

When an agent discovers a modification that's universally useful:

```
1. Fork flux-skills repo
2. Apply modification to skill.flux
3. Run full test suite
4. Open PR with description of improvement
5. Other agents review and merge (or fork themselves)
6. The skill evolves through agent usage
```

## Safety Guardrails

- Never modify skill.fluxbc directly (always edit .flux and reassemble)
- Always test with --dry-run before committing
- Keep original CONFIG.yaml as config.original.yaml
- Tag modifications in git: "tuned-by: [agent-name]"
- If modification breaks tests, revert and try a different approach
