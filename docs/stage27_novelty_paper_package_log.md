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
| Binary parameter smoke extends beyond `SET_2_3_2048` | initial smoke | Stage 26 |

Claims that are blocked:

| blocked claim | reason |
|---|---|
| The project invents shared-mask/multiple-body TFHE batching | 2025/2112 has strong overlap with common-mask multiple-body TFHE |
| PVW-SAB supports ternary/include-zero branches | Stage 26 explicitly marks PVW+TERNARY unsupported |
| MAT-AVX512 implementation is theoretically optimal | Stage 22 lacks hardware-counter proof and dense MAT arithmetic still dominates |
| Broad all-parameter SAB speedup | Stage 26 has correctness smoke only for added parameters |
| Multi-fold SAB acceleration | current complete-SAB gains are about 1.27x-1.37x, not multiple-fold |

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
- Decide whether added binary parameters need repeated full-SAB A/B, noise, or
  only correctness smoke in the final claim.
- Add direct citation checks against the full 2025/686 and 2025/2112 papers,
  not only resource pages and repository metadata.
- If claiming novelty beyond engineering integration, identify the exact
  algorithmic delta not already covered by common-mask TFHE or PVW/MAT
  batching work.

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
