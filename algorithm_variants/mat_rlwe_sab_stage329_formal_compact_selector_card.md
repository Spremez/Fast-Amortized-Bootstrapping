# Stage329: Formal Compact Selector Candidate Card

## Summary

- Parent algorithm: r-body PVW/MAT-SAB.
- Focused module: MAT_TRGSW selector representation for compact/shared-output
  external product.
- Optimization target: reduce dense `(r+1)^2` selector work while preserving
  complete-SAB `T_bootstrap/r` correctness.
- Status labels: `[finite algebra pass] [security/keygen open] [no code permission]`.
- Main hypothesis: semantic-zero dummy selector rows can be skipped by the
  evaluator if production keygen/security proves they leak no forbidden
  structure.

## Mathematical Definition

Let `M` be the dense selector matrix over `r+1` input/output components and
`A` the declared active row set from Stage203. The finite checker verifies:

```text
M_zero x == M_A x
```

when all rows outside `A` are semantic zero, and rejects random dummy rows or
missing active rows.

## Pseudocode

```text
Input: Stage203 equation map, finite vector x
Output: pass/fail rows
1. Build active selector rows from the equation map.
2. Fill inactive rows with zero and compare dense vs active evaluation.
3. Fill inactive rows with random values and require mismatch.
4. Remove one active row and require mismatch.
5. Report proof obligations before production code.
```

## Delta From Original Algorithm

| Original component | Variant component | Relationship | Evidence/status |
| --- | --- | --- | --- |
| Dense MAT_TRGSW rows | active rows plus semantic-zero dummy rows | changes selector representation | finite checker pass only |
| Current exact dense evaluator | evaluator skipping proven dummy rows | potential complexity reduction | proof/keygen/noise open |
| Complete SAB speed claim | none | blocked | no full SAB implementation |

## Complexity Change

- Time: potential row work from `(r+1)^2` to `4r` per gadget level if and only
  if dummy rows are provably skippable.
- Memory: public key may remain dense if dummy random padding is required.
- What must be measured: key size, keygen, noise, and complete `T_bootstrap/r`.

## Theory Dependencies

- Inherited assumptions: Stage203 equation map and Stage249 distribution
  boundary.
- New assumptions: production keygen can realize semantic-zero dummy rows
  without public distinguishers.
- New lemmas needed: keygen/distribution, noise recurrence, and SAB closure.
- Current status: finite algebra pass; production proof open.

## Required Experiments

- Baselines: current exact dense PVW/MAT-SAB and repeated scalar SAB.
- Metrics: complete-SAB `T_bootstrap/r`, correctness, noise, key size, memory.
- Ablations: dummy rows evaluated vs skipped; active-row set negative controls.
- Success criteria: proof obligations close and full SAB A/B improves `T/r`.
- Failure criteria: public distribution is distinguishable or full SAB fails.
