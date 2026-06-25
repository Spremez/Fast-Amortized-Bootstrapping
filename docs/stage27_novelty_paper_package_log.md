# Stage 27 Novelty and Paper Package Log

Date: 2026-06-25

## Status

Stage 27 is started, not complete. The current output is a novelty-risk and
claim-boundary audit based on the project evidence and an initial related-work
scan.

## Sources Checked

- The 2025/686 GitHub entry identifies the base paper as "Fast amortized
  bootstrapping with small keys and polynomial noise overhead", notes it is
  associated with CCS 2025, lists binary parameter families, and warns that
  paper results use an AVX-512 platform:
  <https://github.com/antoniocgj/Fast-Amortized-Bootstrapping>
- The 2025/2112 resource topic describes common-mask ciphertexts with a shared
  mask and multiple message bodies, different LUTs on different encrypted
  messages, and amortized TFHE-style operations:
  <https://askcryp.to/t/resource-topic-2025-2112-sharing-the-mask-tfhe-bootstrapping-on-packed-messages/25443>
- The 2025/696 resource topic describes incomplete-NTT amortized
  bootstrapping as an adjacent acceleration strategy and reports a speedup over
  an earlier Guimaraes et al. amortized bootstrapping algorithm:
  <https://askcryp.to/t/resource-topic-2025-696-faster-amortized-bootstrapping-using-the-incomplete-ntt-for-free/24002>
- TFHE/external-product background was checked through Zama's TFHE deep dive
  and the TFHE overview:
  <https://www.zama.org/post/tfhe-deep-dive-part-3>
  and <https://www.tfhe.com/about>
- GSW/LWE background was checked only for security-claim boundaries:
  <https://www.ccs.neu.edu/home/wichs/class/crypto-fall17/lecture23.pdf>

## Claim Classification

Current claims that are supported:

| claim | status | evidence |
|---|---|---|
| PVW/MAT-SAB implementation exists beside scalar SAB | supported | Stage 5-7, Stage 20 |
| Complete SAB throughput improves over repeated scalar SAB on tested binary targets | engineering-supported | Stage 20 and Stage 22 |
| Active-buffer fusion removes target copyback traffic | supported | Stage 20 |
| Specialized MAT-AVX512 is useful but not theoretically optimal | supported | Stage 22 |
| Current promoted r=2/r=4 path has 50-seed final-output noise support on target binary parameter | supported | Stage 25 |
| Added binary parameters have r=2/r=4 complete-SAB and noise support | small-sample support | Stage 26 5-run/5-seed matrix |

Claims that are blocked:

| blocked claim | reason |
|---|---|
| The project invents shared-mask/multiple-body TFHE batching | 2025/2112 has strong overlap with common-mask multiple-body TFHE |
| PVW-SAB supports ternary/include-zero branches | Stage 26 explicitly marks PVW+TERNARY unsupported |
| MAT-AVX512 implementation is theoretically optimal | Stage 22 lacks hardware-counter proof and dense MAT arithmetic still dominates |
| Broad all-parameter SAB speedup | Stage 26 covers two added binary parameters with small-sample evidence, not all parameters or non-binary branches |
| Multi-fold SAB acceleration | current complete-SAB gains are about 1.22x-1.40x across scoped runs, not multiple-fold |

## Safe Paper Framing

The safe framing is:

```text
We integrate a PVW/MAT shared-mask multi-body external-product path into the
2025/686 sparse amortized bootstrapping implementation and evaluate it as a
systems optimization. The contribution is the SAB-specific integration,
schedule/copyback engineering, AVX512 MAT specialization, and reproducible
complete-SAB evidence under scoped binary parameters.
```

The unsafe framing is:

```text
We invent shared-mask TFHE batching, prove a new external-product primitive,
or accelerate all SAB variants.
```

## Evidence Still Needed Before Manuscript Claim

- Re-run a final consolidated full-SAB performance table after the Stage 26
  parameterized harness refactor.
- Decide whether the added binary parameters' 5-run/5-seed small-sample
  evidence is enough for final scope, or whether a larger statistical campaign
  is needed before manuscript wording.
- Add direct citation checks against the full 2025/686 and 2025/2112 papers,
  not only resource pages and repository metadata.
- If claiming novelty beyond engineering integration, identify the exact
  algorithmic delta not already covered by common-mask TFHE or PVW/MAT
  batching work.

## Full-Source Gate Update

The first full-source access attempt is recorded in
`docs/stage27_full_related_work_gate_log.md` and
`repro/stage27_source_access_matrix.csv`. Direct ePrint/ACM PDF fetches for
2025/686 returned HTTP 403 in this environment, so theorem-level and
algorithm-number citation checking for the base paper remains incomplete.
Public full-text pages for 2025/2112 and 2025/696 were accessible enough to
confirm the current claim boundary: shared-mask/multiple-body TFHE batching is
prior-art risky, while incomplete-NTT amortized bootstrapping is an adjacent
acceleration direction.

## Final Full-SAB Performance Update

The first consolidated final full-SAB performance rerun is recorded in
`docs/stage27_final_full_sab_performance_log.md` and
`repro/stage27_final_full_sab_summary.csv`. After the Stage 26 harness
parameterization, the promoted explicit path still improves complete SAB
throughput on `BINARY SET_2_3_2048` under `spqlios_avx512`:

- r=2: three runs passed correctness, mean speedup `1.171x`, range
  `1.111x-1.285x`;
- r=4: three runs passed correctness, mean speedup `1.401x`, range
  `1.331x-1.472x`.

This supports a scoped engineering throughput claim. It does not support
novelty, non-binary, theoretical-optimality, or all-parameter claims.

## Added-Parameter Scope Update

Stage 26 now includes a 5-run/5-seed matrix for `SET_4_5_2048` and
`SET_2_3_4096`, r=2/r=4, recorded in
`docs/stage26_parameter_perf_noise_log.md` and
`repro/stage26_parameter_perf_noise_avx512_added_binary_r2_r4_runs5_seeds5/`.
All full-SAB correctness gates passed and all final-output noise aggregates had
zero PVW, scalar, and pair failures. Mean speedups ranged from 1.224x to
1.346x, with `SET_4_5_2048` r=2 showing the highest timing variance.

This upgrades the added-parameter evidence from smoke to small-sample support,
but it still does not justify claims for non-binary branches, all parameter
families, or novelty.

## Decision

Status:

```text
PAPER_PACKAGE_STARTED
NOVELTY_CLAIM_BLOCKED_PENDING_FULL_RELATED_WORK
SAFE_ENGINEERING_CLAIM_AVAILABLE
```

Stage 27 can proceed, but paper-level novelty must stay blocked until the full
papers are reviewed and a final consolidated performance/noise/resource package
is produced.
