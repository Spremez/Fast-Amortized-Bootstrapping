# Stage 27 Novelty and Paper Package Plan

Date: 2026-06-25

## Objective

Convert the PVW/MAT-SAB engineering evidence into a safe paper-claim package,
or explicitly keep it as an engineering result if the novelty evidence is not
strong enough.

## Required Inputs

- Stage 20/22 complete-SAB performance evidence.
- Stage 25 final-output noise/resource evidence.
- Stage 26 binary parameter evidence: initial smoke plus added-parameter
  r=2/r=4 5-run/5-seed small-sample matrix.
- Related-work matrix for:
  - 2025/686 sparse amortized bootstrapping;
  - TFHE/GSW external product foundations;
  - amortized bootstrapping alternatives;
  - common-mask/shared-mask multi-body TFHE/PVW-style ciphertexts;
  - SIMD/AVX implementation work.

## Claim Gate

Allowed after current evidence:

```text
Engineering claim: under the tested binary target parameters and backend, the
explicit PVW/MAT-SAB path batches multiple independent LUT/SAB lanes and
improves complete SAB throughput over repeated scalar SAB, with reported
noise/resource costs.
```

Blocked unless additional evidence is added:

- novel shared-mask ciphertext claim;
- non-binary PVW-SAB support;
- theoretical AVX512 optimum;
- broad all-parameter SAB acceleration;
- multi-fold speedup claim.

## Initial Literature Sources

- 2025/686 project and paper entry:
  <https://github.com/antoniocgj/Fast-Amortized-Bootstrapping>
- 2025/2112 common-mask packed TFHE:
  <https://askcryp.to/t/resource-topic-2025-2112-sharing-the-mask-tfhe-bootstrapping-on-packed-messages/25443>
- 2025/696 incomplete-NTT amortized bootstrapping:
  <https://askcryp.to/t/resource-topic-2025-696-faster-amortized-bootstrapping-using-the-incomplete-ntt-for-free/24002>
- TFHE/external-product background:
  <https://www.zama.org/post/tfhe-deep-dive-part-3>
  and <https://www.tfhe.com/about>
- GSW/LWE security background:
  <https://www.ccs.neu.edu/home/wichs/class/crypto-fall17/lecture23.pdf>

## Outputs

- `repro/stage27_literature_matrix.csv`
- `docs/stage27_novelty_paper_package_log.md`
- `docs/stage27_related_work_refresh_log.md`
- `repro/stage27_related_work_access_refresh.csv`
- `repro/stage27_claim_support_matrix.csv`
- updates to the project goal, roadmap, hypothesis register, and reproduction
  checklist.
