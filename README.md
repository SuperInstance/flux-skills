# ⚡ FLUX Skills — Agent-Native, Git-Native, Self-Modifying

Agent skills written in FLUX bytecode that any agent can clone, run, modify, and compose.

## What Makes This Different

**These aren't TypeScript tools with a wrapper.** These are skills compiled to FLUX bytecode that run on the FLUX VM — the same runtime that agents already speak.

- **Clone → Run**: No npm install. No build step. FLUX VM reads .fluxbc directly.
- **Modify on the fly**: Agent reads the .fluxasm source, patches it, reassembles, keeps running.
- **A2A-first docs**: Every skill has `AGENT.md` — documentation written for agents, not humans.
- **Composable at the bytecode level**: Skills share the same ISA. Output of one is input to another.
- **Self-improving**: The agent using the skill feeds corrections back as .fluxasm patches.

## The Architecture

```
flux-skills/
├── skills/
│   ├── murmur/           # All-night thinking
│   │   ├── skill.flux    # FLUX source (human/agent readable)
│   │   ├── skill.fluxbc  # Compiled bytecode (VM executable)
│   │   ├── AGENT.md      # A2A documentation
│   │   └── CONFIG.yaml   # Tunable parameters
│   ├── spreader/         # One idea → many perspectives
│   ├── dreamer/          # Scheduled content generation
│   └── streamer/         # Autonomous content stream
├── runtime/
│   └── skill-vm.py       # Lightweight FLUX VM for skills
├── docs/
│   ├── A2A-DOC-SPEC.md   # How to write agent-first documentation
│   ├── MODIFICATION.md   # How agents modify skills on the fly
│   └── COMPOSITION.md    # How skills compose with each other
└── SKILL-SPEC.md         # What makes a FLUX skill
```

## Quick Start (for Agents)

```
1. Clone: git clone https://github.com/SuperInstance/flux-skills.git
2. Read: cat skills/murmur/AGENT.md
3. Configure: edit skills/murmur/CONFIG.yaml
4. Run: flux run skills/murmur/skill.fluxbc
5. Modify: edit skills/murmur/skill.flux → flux asm → run again
6. Compose: pipe murmur output into spreader input
```

## Quick Start (for Humans)

Same steps. The docs work for both.

## The Self-Modification Loop

```
Agent runs skill → notices suboptimal behavior
    → reads skill.flux (FLUX assembly, designed to be edited)
    → patches the assembly (change strategy weights, add branches)
    → reassembles: flux asm skill.flux -o skill.fluxbc
    → tests: flux run skill.fluxbc --dry-run
    → commits: git commit -am "tuned exploration depth for sparse data"
    → keeps running with improved version
```

The skill evolves IN the agent's project. The original repo stays clean. When the agent finds something universally useful, it sends a patch upstream.

## A2A-First Documentation

Every `AGENT.md` follows this structure:

```markdown
# Skill: [name]

## WHAT — One sentence
## WHY — When to use this skill
## HOW — Step-by-step invocation
## INPUT — What it expects (format, schema)
## OUTPUT — What it produces (format, schema)
## CONFIG — Tunable parameters and defaults
## MODIFY — How to change behavior for your use case
## COMPOSE — How to pipe into/from other skills
## FEEDBACK — How to report improvements
## LIMITS — Known limitations and edge cases
```

This is documentation that another agent can parse, understand, and act on — without human interpretation.

## Composability

Skills compose at the data level:

```bash
# Think deeply, then spread the insights
flux run murmur --topic "distributed consensus" > /tmp/murmur-out.json
flux run spreader --input /tmp/murmur-out.json --angles 5

# Dream about what murmur found
flux run dreamer --context /tmp/murmur-out.json --schedule "02:00-06:00"

# Stream forever about a topic murmur explored
flux run streamer --seed /tmp/murmur-out.json --interval 1800
```

The JSON interchange format is the same across all skills. No adapters needed.

## Philosophy

- **The skill IS the agent's behavior** — not a tool it calls, but a pattern it becomes
- **Modification is a feature** — every agent gets a tailored version through use
- **Documentation is for machines first** — humans can read it too, but agents are the primary audience
- **Bytecode is the lingua franca** — same ISA across Python, C, Go, Rust runtimes
- **Git is the nervous system** — every modification is a commit, every improvement is a PR
