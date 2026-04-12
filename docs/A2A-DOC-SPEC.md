# A2A Documentation Specification v1.0

## What Is A2A-First Documentation?

Documentation written for agents reading agents. The primary audience is an AI agent trying to understand, use, modify, or compose with another agent's skill. Humans can read it too, but the structure optimizes for machine parsing.

## Why This Matters

Traditional docs assume:
- A human is reading
- Context is accumulated linearly
- Examples are illustrative, not executable

A2A docs assume:
- An agent is parsing sections independently
- Context is extracted programmatically
- Examples are copy-pasteable commands with expected output

## Required Sections (AGENT.md)

Every AGENT.md must have exactly these sections in this order:

### WHAT
One sentence. What this skill does. No preamble, no context setting.

Bad: "Murmur is an innovative thinking agent that..."
Good: "Explores a topic through multiple strategies, building a knowledge tensor over time."

### WHY
When to use this skill. Bullet list of use cases. Also: when NOT to use it.

### HOW
Copy-pasteable invocation commands. Include the most common usage pattern. No prose.

### INPUT
Schema of expected input. JSON schema preferred. Include field names, types, and whether required.

### OUTPUT
Schema of output. Must include at least one example. JSON format for composability.

### CONFIG
Table of tunable parameters: name, type, default, what it affects, valid range. Machine-parseable format:

```
PARAM: max_thoughts | TYPE: int | DEFAULT: 50 | AFFECTS: total thoughts | RANGE: 1-1000
```

### MODIFY
How to change behavior. Must include:
1. Which file to edit
2. Which section/lines
3. Before/after example
4. Reassembly command

This section is what enables self-modification. An agent reads this, edits the source, reassembles, and keeps running.

### COMPOSE
How to pipe into/from other skills. Must include:
1. Input format from other skills this one accepts
2. Output format this skill produces that others accept
3. At least 2 composition examples with full commands

### FEEDBACK
How to report improvements. Where to open issues. What to include in the report.

### LIMITS
Known limitations. Every limitation must be actionable — either a workaround or a plan.

## Writing Guidelines

1. **No prose in required sections** — use structured format (tables, code blocks, schemas)
2. **Every example must be runnable** — no pseudocode, no "you would typically..."
3. **Include failure modes** — what happens when input is malformed, budget is exhausted, etc.
4. **Version pin everything** — `flux_isa_version: "2"` so agents know compatibility
5. **Keep it under 200 lines** — agents have context limits too

## Anti-Patterns

- Marketing language ("innovative", "powerful", "cutting-edge")
- Human-centric framing ("you might want to...", "it's easy to...")
- Prose paragraphs in required sections
- Examples that require external state not described in INPUT
- CONFIG defaults that produce no output (every default should be useful)
