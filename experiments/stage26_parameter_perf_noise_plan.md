# Stage 26 Parameter Performance/Noise Plan

Date: 2026-06-25

## Objective

Extend Stage 26 beyond target correctness smoke by running complete-SAB
performance and final-output noise gates on added binary parameters.

## Scope

```text
FFT_LIB=spqlios_avx512
KEY=BINARY
MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true
SAB_PVW_ACTIVE_BUFFER_FUSION=true
```

Initial smoke scope:

- `SET_4_5_2048`, r=2 and r=4;
- `SET_2_3_4096`, r=2;
- one process run for complete-SAB A/B;
- one deterministic final-output noise seed.

This is a parameter-smoke gate, not statistical performance evidence.

Executed follow-up scope:

- `SET_4_5_2048` and `SET_2_3_4096`, r=2 and r=4;
- five process runs for complete-SAB A/B per case;
- five deterministic final-output noise seeds per case.

This upgrades added binary parameters to small-sample support. It is still not
equivalent to the main target's 50-seed final-output noise campaign and should
not be used for all-parameter or non-binary claims.

## Gate

- Complete `sab_pvw_*` target benchmark must report `Pass`.
- Final-output noise must report zero PVW, scalar, and pair failures.
- Any positive speedup is labeled smoke unless repeated process runs and
  multi-seed noise are added.
- Non-binary PVW remains unsupported and out of scope.

## Failure Handling

- A correctness or noise failure blocks any broad parameter claim.
- A script failure after raw gates complete must be recorded and fixed before
  the script is reused.
- If only one added parameter improves, final claims must stay parameter-scoped.
