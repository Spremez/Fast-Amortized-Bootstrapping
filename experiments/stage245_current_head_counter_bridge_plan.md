# Stage245 Current-Head Counter Bridge Plan

## Objective

Bridge Stage226 native counter evidence to current head only if executable
MAT/PVW-SAB code is unchanged.

## Command

```text
python scripts/build_stage245_current_head_counter_bridge.py
```

## Gates

- Inputs from Stage226 exist.
- `git diff --name-status f2b753f..HEAD -- main.c Makefile include src` is empty.
- Stage226 decision is pass.
- Claim boundary states attribution-only reuse.
