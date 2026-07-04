# mat_rlwe_sab_stage332_paper_claim_card

## Summary

- Parent algorithm: direct PVW/MAT-SAB for 2025/686 sparse amortized
  bootstrapping.
- Focused module: scoped result packaging.
- Optimization target: complete `T_bootstrap/r`.
- Status: `PASS_STAGE332_SCOPED_PAPER_RESULT_PACK`.

## Paper-Safe Claim

For `BINARY SET_2_3_2048` include-zero on `spqlios_avx512`, `r=4` direct
PVW/MAT-SAB achieves `1.747647x` amortized complete-SAB throughput over
repeated scalar SAB, measured by `T_bootstrap/r`.

## Required Boundaries

- Do not claim single-bootstrap latency speedup.
- Do not claim theoretical optimality.
- Do not claim compact selector security or acceleration.
- Do not claim novelty until Stage333 verifies real related work.
