primary_plane: 2
reads_from: [3, 4]
writes_to: [2]
floor: 2
ceiling: 4
compilers:
  - name: deepseek-chat
    from: 4
    to: 2
    locks: 7
reasoning: |
  Flux-skills is the skill system for the FLUX VM operating at Plane 2 (bytecode skills).
  Skills are compiled to FLUX bytecode for sandboxed execution, reading from Structured IR
  (3) or Domain Language (4) specifications. The ceiling at 4 reflects that skills are
  defined in domain-specific notation, not natural language.

  Skills are bytecode programs (2) that agents can load and execute safely within the
  FLUX VM. This allows dynamic skill addition without recompiling the base engine.
  The compiler with 7 locks ensures skills are portable and consistent across model
  families, while the bytecode format provides execution isolation.
