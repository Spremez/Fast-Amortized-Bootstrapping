# Stage109 Body-Linear Invariant Gate

Date: 2026-07-03

## Decision

`PASS_STAGE109_BODY_LINEAR_BLOCKED_CURRENT_SELECTOR_FORMAT`

Stage109 checks whether V106-B can be implemented as a local loop-level
body-linear MAT external-product optimization in the current
`MAT_TRGSW_DFT` format. The answer is no: the current selector rows are
full PVW_TMLWE encryptions of zero with diagonal gadget injection, so
off-lane ciphertext terms cannot be skipped without a new selector/key
format and proof.

## Summary Gates

| gate | status | metric | value | detail |
|---|---|---|---|---|
| stage109_source_invariants | PASS | invariant_rows | 8 | Source-level invariants extracted from MAT/PVW implementation. |
| stage109_operation_model | PASS | dense_products_r1_r2_r4_r6_r8 | 4;9;25;49;81 | Current k=1,l=1 MAT external product is dense row-output. |
| stage109_body_linear_decision | PASS_STAGE109_BODY_LINEAR_BLOCKED_CURRENT_SELECTOR_FORMAT | V106-B_policy |  | Current MAT_TRGSW_DFT cannot support body-linear product skipping as a loop-only change. |

## Invariant Matrix

| id | status | invariant | implication |
|---|---|---|---|
| I109-1 | PASS | PVW_TMLWE has one shared mask vector and r body polynomials. | The r bodies are tied through the same mask coordinates and per-body secret columns. |
| I109-2 | PASS | PVW_TMLWE encryption fills every body with a zero-encryption relation before message add. | Dropping off-lane body ciphertext terms breaks the zero-encryption cancellation unless a new key/selector format proves otherwise. |
| I109-3 | PASS | MAT_TRGSW rows are l*(k+r), not one independent scalar TRGSW per body only. | For k=1,l=1 the current selector has r+1 encrypted rows. |
| I109-4 | PASS | Each MAT_TRGSW row is first sampled as a full PVW_TMLWE encryption of zero. | Even diagonal plaintext gadget rows carry full encrypted zero components. |
| I109-5 | PASS | The plaintext gadget injection is diagonal, but the ciphertext carrier remains full PVW. | Diagonal plaintext alone is insufficient to skip encrypted off-lane zero terms. |
| I109-6 | PASS | The generic MAT external product multiplies every decomposition row into every output component. | Current implementation shape is dense (k+r)^2 for k=1,l=1. |
| I109-7 | PASS | No selector metadata exists to certify plaintext/off-lane zero terms for safe skipping. | A body-linear shortcut would require a new selector/key format or a proof-carrying metadata layer. |
| I109-8 | BLOCKED_CURRENT_FORMAT | Current V106-B body-linear implementation is not safe as a local loop-only change. | Do not implement body-linear by skipping ciphertext products in the existing MAT_TRGSW_DFT format. |

## Operation Model

| r | rows | outputs | current dense products | dense products/lane | body-linear target products |
|---:|---:|---:|---:|---:|---:|
| 1 | 2 | 2 | 4 | 4.000 | 3 |
| 2 | 3 | 3 | 9 | 4.500 | 5 |
| 4 | 5 | 5 | 25 | 6.250 | 9 |
| 6 | 7 | 7 | 49 | 8.167 | 13 |
| 8 | 9 | 9 | 81 | 10.125 | 17 |

## Next Gate

The next non-theory-loop step is a finite selector/key-format design gate:
define the minimal additional metadata or alternative encryption format
that makes body-linear skipping mathematically valid, then test it with a
small r=2 equivalence harness before any AVX512 optimization work.