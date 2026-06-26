# pvw_sab_sparse_selector_shortcut: Sparse Selector Shortcut

## Summary

- Parent algorithm: 2025/686 binary sparse amortized bootstrapping with the
  explicit `sab_pvw_*` PVW/MAT path.
- Focused module: MAT_TRGSW external product inside PVW CMUX/NCMUX.
- Optimization target: reduce dense `(1+r)^2` MAT external-product work.
- Status labels: rejected under current evidence; theory/security gap.
- Main hypothesis: using SAB monomial selector structure could skip encrypted
  MAT selector work and improve full SAB throughput.

## Mathematical Definition

Current PVW/MAT CMUX evaluates an encrypted selector bit through
`MAT_TRGSW_DFT` against a shared-mask multi-body accumulator. The proposed
shortcut would add selector-bit-dependent row/output skipping.

Under the current public evaluation state, the selector bit is not plaintext;
only an encryption of the bit is available. Therefore there is no safe
row/output skip predicate in the existing data structure.

## Pseudocode

```text
Input: PVW accumulator p, encrypted MAT_TRGSW_DFT selector e
Output: updated accumulator p'
1. Do not inspect ciphertext coefficients as a sparsity predicate.
2. Do not attach plaintext gap-bit metadata to e without a leakage proof.
3. Fall back to the current dense MAT external-product path.
```

## Delta From Original Algorithm

| Original component | Variant component | Relationship | Evidence/status |
| --- | --- | --- | --- |
| Dense encrypted MAT external product | Plaintext selector-bit skipping | changes key metadata/security boundary | rejected for current implementation |
| Secret-dependent gap bits encrypted in bootstrapping key | Public skip metadata | possible leakage | requires new proof before code |
| Existing scalar SAB and explicit PVW path | Unchanged | preserves baseline | required invariant |

## Complexity Change

- Time: could reduce constant factors only if a safe skip predicate exists.
- Memory: could reduce temporary/output traffic only with a changed layout.
- Communication or IO: may increase or leak through key metadata.
- What must be measured: full SAB A/B, key size, memory, and leakage-sensitive
  metadata footprint.

## Theory Dependencies

- Inherited assumptions: encrypted selector bits remain hidden under the
  current bootstrapping key representation.
- Relaxed/new assumptions: any public selector metadata must be proven safe.
- Proof steps affected: key privacy, noise distribution, and CMUX correctness.
- New lemmas needed: public metadata non-leakage or a revised security model.
- Current status: not ready for implementation.

## Potential Failure Reasons

- Failure mode: leaks secret-dependent monomial gaps.
- Trigger condition: plaintext skip metadata is emitted with the bootstrapping
  key.
- How to detect: key-format audit and proof review, not benchmark output.
- Mitigation or follow-up: design a new metadata policy first, then run staged
  correctness/noise gates.

## Required Experiments

- Baselines: current active-buffer PVW/MAT-SAB and repeated scalar SAB.
- Metrics: full SAB latency, throughput per lane, key size, memory, keygen
  time, noise/failure rate.
- Ablations: r=1/2/4, metadata on/off, backend controlled.
- Complexity runs: compare exact external-product counts and per-stage profile.
- Robustness runs: multi-seed final-output and stage-level noise.
- Success criteria: correctness/noise unchanged and complete-SAB speedup beyond
  current promoted path.
- Failure criteria: any leakage/proof gap, correctness failure, or neutral full
  SAB performance.

## Paper Contribution Candidate

No paper contribution is currently claimable for this candidate. A future
version would need source-anchor review, a leakage/security argument, and
complete-SAB evidence before it could be described as an algorithmic
improvement.
