# mat_rlwe_sab_stage330_reconciled_direct_dft_claim

## Summary

- Parent algorithm: 2025/686 sparse amortized bootstrapping with PVW/MAT-RLWE
  multi-body accumulator path.
- Focused module: complete SAB evidence and claim boundary for direct
  sub-decomposition-to-DFT materialization.
- Optimization target: amortized complete SAB `T_bootstrap/r`.
- Status labels: `PASS_SCOPED_HISTORICAL_HIGHSTAT`, `PASS_CURRENT_HOTCODE_ENGINEERING`,
  `PARTIAL_RERUN_REQUIRED_FOR_STRICT_CURRENT_HEAD_PAPER_TABLE`.
- Main hypothesis: using MAT/RLWE `r` body lanes amortizes the SAB schedule over
  multiple plaintext bits, and direct DFT materialization reduces complete-SAB
  per-lane time relative to repeated scalar SAB.

## Delta From Original Algorithm

| Original component | Variant component | Relationship | Evidence/status |
| --- | --- | --- | --- |
| repeated scalar SAB over `r` bits | one PVW/MAT-SAB run with `r` body lanes | changes ciphertext data structure and amortizes schedule | Stage296/321 complete `T_bootstrap/r` |
| delayed torus-to-DFT materialization | direct sub-decomposition-to-DFT path | implementation/schedule optimization within PVW/MAT-SAB | Stage296 high-stat; Stage321 current-hot-code |

## Complexity Change

- Time: measured as `T_bootstrap/r`; current supported speedup is in the
  `1.735849x` to `1.745361x` band for `BINARY SET_2_3_2048`, `r=4`,
  `spqlios_avx512`, include-zero.
- Memory/key: direct DFT does not add a key format; Stage297 records local RSS
  side condition for the selected/direct comparison.
- What must still be measured: exact current-head >=10 run table if paper
  wording requires strict current-head statistical evidence.

## Paper Contribution Candidate

`[experiment supported, scoped]` PVW/MAT-SAB should be reported using
amortized complete-SAB time per plaintext bit/lane, not kernel-only speedup.

`[not yet supported]` The construction is theoretically optimal among all
MAT/RLWE SAB algorithms, or compact selector variants are secure and faster.
