# H14-C1: Backend FromDFT-Add Materialization

## Summary

- Parent algorithm: PVW/MAT-SAB binary bootstrapping path.
- Focused module: CMUX materialization after MAT external product.
- Optimization target: complete SAB throughput through reduced materialization
  memory traffic.
- Status labels: `[Stage87 preflight positive]`, `[implementation-only
  constant-factor hypothesis]`, `[not promoted]`.
- Main hypothesis: moving the add-back inside the inverse DFT materialization
  backend reduces torus-domain load/store traffic relative to the current
  wrapper-level `pvmtmlwe_from_DFT_add` path. Stage87 records a positive
  one-run r=6 complete-SAB smoke, but repeated/noise/resource gates remain
  required.

## Mathematical Definition

The inherited CMUX update is:

```text
out = in1 + FromDFT(MAT_TRGSW_DFT * (in2 - in1)).
```

The variant does not change the algebraic update. It changes only the
materialization operator:

```text
FromDFTAdd_backend(dft_poly, addend_poly) =
    FromDFT(dft_poly) + addend_poly
```

The existing wrapper computes `FromDFT(dft_poly)` into `out` and then adds
`addend_poly` in a second torus pass. The variant requires the backend to emit
`out[i] = inverse_dft_i + addend[i]` during the inverse materialization store.

## Pseudocode

```text
Input: DFT accumulator tmp_dft, torus addend in1, output out
Output: out = in1 + FromDFT(tmp_dft)
1. For each mask/body polynomial in the PVW sample:
2.   Run inverse DFT until coefficient blocks are ready to write.
3.   Add the matching torus coefficient block from in1 before or during store.
4.   Store the final torus block into out.
```

## Delta From Original Algorithm

| Original component | Variant component | Relationship | Evidence/status |
| --- | --- | --- | --- |
| `pvmtmlwe_from_DFT_add()` wrapper | backend `FromDFTAdd` materialization callback under `SAB_PVW_BACKEND_FROM_DFT_ADD` | implements same equation with less torus pass traffic | implemented by Stage87 |
| scalar SAB | unchanged | baseline preserved | required invariant |
| MAT key format | unchanged | key/security boundary preserved | required invariant |
| Stage18/23 wrapper fusion | backend-boundary callback | different implementation layer | Stage18/23 neutral guard |

## Complexity Change

- Time: asymptotically unchanged; constant-factor memory traffic may drop for
  the add-back portion.
- Memory: no additional hot-path accumulator array should be required.
- Communication or IO: none.
- What must be measured: materialization microbench, complete SAB A/B, and
  whether any backend-specific cost moves into FFT arithmetic.

## Theory Dependencies

- Inherited assumptions: CMUX algebra, PVW/MAT external product, encrypted
  selector semantics, current binary SAB schedule.
- Relaxed/new assumptions: none at the protocol level.
- Proof steps affected: none if the backend callback is bit-exact with
  `FromDFT(dft) + addend`.
- New lemmas needed: implementation equivalence lemma for backend callback.
- Current status: flagged Stage87 preflight passes and opens Stage88 only.

## Potential Failure Reasons

- Failure mode: backend callback is neutral because inverse FFT arithmetic
  dominates memory traffic.
- Trigger condition: materialization microbench improves but full SAB does not.
- How to detect: same-backend full SAB A/B and profile attribution.
- Mitigation or follow-up: reject or keep as kernel-only evidence; consider
  H14-C3 only if sub share remains material.

## Required Experiments

- Baselines: current explicit PVW/MAT-SAB path with
  `MAT_TRGSW_AVX512_RGT4_FUSED=true` and current `pvmtmlwe_from_DFT_add`.
- Datasets/parameters: `BINARY SET_2_3_2048`, r=4 as continuity check, r=6 as
  post-H11/Stage82 target.
- Metrics: materialization us, full SAB mean/min/max speedup, correctness,
  final-output noise, key size, RSS.
- Ablations: wrapper-level fused path versus backend callback; r=4 versus r=6.
- Complexity runs: profile from_DFT/add/sub shares before and after.
- Stage87 smoke result: wrapper r=6 PVW latency `40196035.000 us`, backend r=6
  PVW latency `38284667.000 us`, backend-vs-wrapper latency ratio
  `1.049925x`.
- Robustness runs: repeated full-SAB A/B and deterministic target gate.
- Statistical checks: repeated process-level samples, mean/min/max, and no
  single-run promotion.
- Success criteria: complete SAB repeated A/B improves over current explicit
  path while correctness/noise/resource gates pass.
- Failure criteria: only microbench improves, full SAB is neutral/negative, or
  the implementation requires key-format or selector-visibility changes.

## Paper Contribution Candidate

Conservative current wording:

```text
[preflight positive] We implement a backend-level FromDFT-add materialization
callback behind an explicit flag and observe a positive r=6 complete-SAB
one-run smoke against the wrapper-level fused baseline.
```

Do not write as a bootstrapping acceleration claim until complete SAB A/B
passes.
