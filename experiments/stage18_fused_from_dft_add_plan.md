# Stage 18 Fused From-DFT Add Plan

Date: 2026-06-25

## Objective

Test the first CMUX scratch-fusion candidate suggested by the Stage 18 profile:
replace

```text
pvmtmlwe_from_DFT(tmp, dft)
pvmtmlwe_add(out, tmp, in1)
```

with

```text
pvmtmlwe_from_DFT_add(out, dft, in1)
```

when `out != in1`.

## Scope

The new path is gated by:

```text
SAB_PVW_FUSED_FROM_DFT_ADD=true
```

It is not a default optimization.

## Correctness Gate

- staged kernel/API gate under `SAB_PVW_KERNEL_TEST=true`;
- target full-output gate under `SAB_PVW_TARGET_TEST=true`;
- one-run full SAB smoke for r=2 and r=4 before any repeated claim.

## Performance Gate

- the first claim is smoke only;
- repeated promotion requires Stage 16-style three-process sweeps;
- if speedup does not improve over Stage 16, preserve as negative evidence.

## Failure Handling

- if aliasing is detected (`out == in1`), the code falls back to the original
  two-step path;
- if correctness fails, disable the flag and do not reuse the helper in CMUX.

## Profile Note

When fused mode and `SAB_PVW_BODY_PROFILE` are both enabled, the combined
from-DFT/add-back time is reported under `cmux_from_dft_us`. `cmux_add_calls`
is still incremented to preserve call-count invariants, but `cmux_add_us` does
not double-count the fused time.
