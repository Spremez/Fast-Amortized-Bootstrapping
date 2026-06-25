# Stage 26 Parameter and Branch Generalization Plan

Date: 2026-06-25

## Objective

Determine whether the current explicit PVW/MAT-SAB path can move beyond the
single `BINARY SET_2_3_2048` target without overclaiming unsupported SAB
branches.

## Required First Fix

Before this stage, the PVW target harness was hard-coded to:

```text
in_N=2048, out_N=2048, h=39, r_prec=7, msg_prec=3
```

Changing `PARAM=...` at build time did not actually change the PVW target
gate. Stage 26 therefore first parameterizes the PVW target harness with the
same binary `SET_*` values used by the scalar test path.

## Smoke Matrix

Initial binary target-smoke scope:

| param | purpose |
|---|---|
| `SET_2_3_2048` | target baseline regression |
| `SET_4_5_2048` | same `N`, different `h`, message precision, and KS parameters |
| `SET_2_3_4096` | larger input `N` and different `r_prec` |

Initial branch-scope check:

- `KEY=TERNARY` with PVW target gate must be recorded as unsupported.
- `KEY=TERNARY` scalar build should remain possible, proving the PVW guard
  does not disable the scalar code path.

## Command

```sh
STAGE26_OUT_DIR=repro/stage26_parameter_branch_smoke_avx512 \
bash scripts/run_stage26_parameter_target_smoke.sh
```

Default backend:

```text
FFT_LIB=spqlios_avx512
MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true
SAB_PVW_ACTIVE_BUFFER_FUSION=true
```

## Gate

Pass:

- all binary target smoke runs report `SAB_PVW target full bootstrap gate: Pass`;
- summary records the expected `h` and `r_prec` for each parameter;
- PVW+TERNARY fails with the explicit binary-only guard;
- scalar TERNARY build passes.

Fail:

- any binary parameter correctness mismatch;
- any parameter silently falls back to `SET_2_3_2048`;
- non-binary PVW appears to pass without a dedicated ternary/include-zero
  implementation.

## Claim Boundary

Passing this stage only supports a binary-parameter generalization smoke. It
does not prove performance scaling, full noise robustness for the new
parameters, or support for ternary/include-zero PVW-SAB.
