# Stage88 H14 Backend Repeated Gates Plan

Date: 2026-06-26

## Goal

Decide whether the Stage87 H14-C1 backend `FromDFT+add` materialization
candidate should remain a promotion candidate after repeated complete-SAB,
final-output noise, and resource gates.

## Command

```bash
bash scripts/run_stage88_h14_backend_repeated_gates.sh
```

Default configuration:

- `FFT_LIB=spqlios_avx512`
- `SAB_PVW_BENCH_R=6`
- `SAB_PVW_BENCH_REPS=1`
- `STAGE88_FULL_SAB_RUNS=3`
- `STAGE88_NOISE_SEED_COUNT=3`
- `STAGE88_RESOURCE_RUNS=1`

## Gates

- Stage87 precondition:
  `PASS_STAGE87_H14_BACKEND_FROM_DFT_ADD_PREFLIGHT_PROMOTION_CANDIDATE`.
- Repeated complete-SAB:
  wrapper fused `FromDFT+add` and backend `FromDFT+add` both pass, with
  backend-vs-wrapper latency ratio reported over paired runs.
- Backend-vs-scalar:
  backend PVW remains faster than repeated scalar SAB.
- Noise:
  backend final-output noise/correctness has zero PVW, scalar, and pair
  failures over the configured seeds.
- Resource:
  backend key size, keygen time, and RSS are reported against repeated scalar;
  RSS over `1.25x` is treated as review-required.

## Decision Policy

- `PASS_STAGE88_H14_BACKEND_REPEATED_GATES_RECORDED_PROMOTION_CANDIDATE`:
  repeated backend-vs-wrapper is positive, backend-vs-scalar is positive,
  noise passes, and resource passes.
- `PASS_STAGE88_H14_BACKEND_REPEATED_GATES_RECORDED_REVIEW_REQUIRED`:
  usable evidence exists, but min-run or resource overhead requires review.
- `PASS_STAGE88_H14_BACKEND_REPEATED_GATES_RECORDED_NOT_PROMOTED`:
  evidence is valid, but the candidate does not justify promotion.
- `FAIL_STAGE88_H14_BACKEND_REPEATED_GATES`:
  correctness, noise, resource, or required evidence is missing or failed.

Stage88 does not change scalar SAB or default PVW behavior. Any positive
decision opens a promotion-policy integration stage rather than changing
defaults directly.
