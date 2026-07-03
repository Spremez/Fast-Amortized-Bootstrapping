# Stage109 Body-Linear Invariant Gate Plan

Date: 2026-07-03

## Objective

Decide whether V106-B body-linear MAT external product can be pursued as a
local kernel rewrite under the current `MAT_TRGSW_DFT` key/selector
format.

## Gate

- Extract source-level invariants for PVW_TMLWE, MAT_TRGSW row generation,
  gadget injection, decomposition order, and external-product loops.
- If selector rows are full encrypted PVW objects without skip metadata,
  block loop-only body-linear implementation.
- If a safe invariant exists, open a small correctness harness before any
  performance work.

## Command

```bash
python scripts/build_stage109_body_linear_invariant_gate.py
```