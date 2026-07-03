# Stage112 Selector/Key-Format Gate Plan

Date: 2026-07-03

## Objective

Convert the Stage109 source-level blocker into a finite selector/key-format
design gate for body-linear MAT external product.

## Command

```bash
python scripts/build_stage112_selector_format_gate.py
```

## Gate

- Provide a concrete shared-mask phase counterexample for loop-only
  off-lane skipping.
- Classify candidate new formats.
- Select a finite r=2 simulator gate instead of continuing theory-only
  discussion.