# Stage127 Isolated Compact EP Kernel Gate Plan

Date: 2026-07-03

## Objective

Turn the Stage126 compact selector encryption/noise semantics into a
reusable isolated DFT external-product kernel with explicit scratch,
without modifying MOSFHET headers or `sab_pvw_*`.

## Command

```bash
python scripts/build_stage127_isolated_compact_ep_kernel_gate.py
```

## Falsification Criteria

- MOSFHET build or probe compile fails;
- kernel DFT components diverge from coefficient reference beyond tolerance;
- kernel phase fails to match the modeled noisy reference;
- body-only kernel does not fail as a negative control;
- compact DFT-term ratio is not positive or total-term ratio falls below 1.0.

Passing this stage permits only a MOSFHET-adjacent compact EP API boundary
stage, not SAB hot-path integration.
