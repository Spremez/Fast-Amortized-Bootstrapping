# Stage108 Body-Major Layout Gate Plan

Date: 2026-07-03

## Objective

Run the first post-Stage107 bounded implementation gate for the MAT-RLWE SAB
research track. Stage107 showed that the current MAT external-product kernels
are still dense row-output accumulations, so Stage108 tests a layout-only
variant before attempting the theory-critical body-linear V106-B path.

The tested hypothesis is V106-D:

```text
For r=6, a body-major MAT external-product loop may improve coefficient
locality compared with the existing tile4 and fulltile r>4 kernels without
changing selector/key semantics or the scalar/default SAB path.
```

## Implementation Scope

- Add `MAT_TRGSW_AVX512_R6_BODYMAJOR=true` as an explicit build flag.
- Dispatch the new r=6 body-major path only for `k=1`, `l=1`, and `r=6`.
- Preserve scalar/default SAB and all promoted explicit paths.
- Keep the experiment reversible and do not change key format.

## Gates

Correctness gate:

- `MAT_TRGSW/PVW r>4 kernel test: Pass` must be present for tile4, fulltile,
  and bodymajor builds.

Performance gate:

- Compare `dft_output` and `full_output` kernel timings for r=6 and r=8.
- Treat bodymajor as positive only if it beats both tile4 and fulltile on the
  r=6 kernel comparison.
- Do not promote to a complete-SAB claim without positive complete-SAB
  `T_total/r` evidence.

Stop rule:

- If bodymajor is correct but not performance-positive versus existing layouts,
  record it as a negative ablation and move to V106-B invariant analysis or a
  counter-backed layout explanation. Do not continue blind body-major tuning.

## Reproduction Command

```bash
bash scripts/run_stage108_bodymajor_layout_gate.sh
```

Optional complete-SAB smoke:

```bash
STAGE108_RUN_FULL_SAB=1 bash scripts/run_stage108_bodymajor_layout_gate.sh
```
