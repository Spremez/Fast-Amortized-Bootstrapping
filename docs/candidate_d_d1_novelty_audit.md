# Candidate D D1 Full-Text Novelty Audit

## Decision

`BLOCK_D1_REQUIRED_FULLTEXT_OR_REVIEW_MISSING`

The gate is fail closed. 8 of nine mandatory primary sources are locally
hash-bound and claim-anchored. Missing or invalid mandatory sources: `NTRU_AMORT_2026_068`.
Candidate D therefore does not advance to D2, and no algorithm hot-path change is authorized by this audit.

## Source Evidence

| source | local verification | pages | claim classification |
|---|---|---:|---|
| FAB_2025_686 | FULLTEXT_REVIEWED | 1-34 | TARGET_SAB_PROTOCOL_NOT_PRIOR_ART_AGAINST_ITSELF |
| SHARING_MASK_2025_2112 | FULLTEXT_REVIEWED | 1-47 | SAME_COMMON_MASK_CIPHERTEXT_SEMANTICS_DIFFERENT_SAB_OPERATOR_QUESTION |
| BATCHBOOT_SEC26 | FULLTEXT_REVIEWED | 1-20 | COMPETING_BATCHED_TFHE_COST_REDUCTION_COMPOSITION_MUST_BE_TESTED |
| FDFB2_2024_1376 | FULLTEXT_REVIEWED | 1-21 | SAME_BROAD_LATE_BOUND_MULTI_FUNCTION_OPERATOR_DISTINCT_SAB_CLOSURE_UNRESOLVED |
| MULTIVALUE_2018_622 | FULLTEXT_REVIEWED | 1-21 | ADJACENT_MULTI_OUTPUT_LUT_PRIOR_ART_NOT_SAB_OPERATOR_CLOSURE |
| MOSFHET_2022_515 | FULLTEXT_REVIEWED | 1-22 | IMPLEMENTATION_AND_MULTI_VALUE_PRIOR_ART_NOT_COMPLETE_SAB_OPERATOR_CLOSURE |
| NTRU_AMORT_2026_068 | FULLTEXT_MISSING | n/a | MANDATORY_POST_FAB_SOURCE_UNREVIEWED |
| BATCH_BOOT_I | FULLTEXT_REVIEWED | 1-32 | THEORETICAL_BATCH_BOOTSTRAPPING_PRIOR_ART_DIFFERENT_OPERATOR_OBJECT |
| BATCH_BOOT_II | FULLTEXT_REVIEWED | 1-32 | THEORETICAL_AMORTIZED_BOOTSTRAPPING_PRIOR_ART_DIFFERENT_OPERATOR_OBJECT |

The PDF and extracted-text files remain outside git under
`references/candidate_d_fulltext/`. Their expected SHA-256 values, page ranges,
claim classes, and short paraphrased anchors are bound by
`literature/candidate_d_source_registry.json`.
The canonical text extraction profile is WSL/Linux Poppler
`pdftotext 24.02.0 -layout`; a different text byte stream does not silently
replace a reviewed extraction.

## Concrete Distinct Claim

Status: `TESTABLE_NOT_PROVEN`

- SAB operator theorem to falsify: For binary 2025/686 SAB, the LUT-independent encrypted update state closes under a fixed basis Gamma with |Gamma| <= 4, and public LUT binding occurs after the sparse schedule using only standard RLWE/GGSW objects.
- Complete complexity/resource result to falsify: Including late binding, extraction, packing key switching, keys, scratch, and noise, Candidate D must replace the exact-dense B1 selector with complete online selector work independent of r or otherwise subquadratic in r.
- Complete implementation endpoint: For BINARY SET_2_3_2048 at r=4, complete T_bootstrap/(r*N_active) must project at least 10% better than B1, later attain a paired 95% CI lower bound of at least 5%, pass absolute correctness/noise/resource gates, and compare or compose with same-backend B2 BatchBoot.

## Claim-Level Answers

1. FDFB2 already exposes the broad late-bound multi-function operator: its reviewed abstract and Section 3 claim an arbitrary number of functions and multiple functions at the cost of one bootstrap.
2. FDFB2 covers arbitrary functions at constant additional cost at its stated
   abstraction level. Candidate D may not claim that broad idea as novel.
3. A Candidate D contribution remains testable only as a SAB-specific bounded
   semilinear operator closure with a different complete complexity/resource
   result and a falsifiable complete-SAB endpoint.
4. Sharing the Mask already covers the shared-mask, multiple-body ciphertext semantics and extension of FHEW/TFHE operations. Common-mask ciphertexts are prior art, not Candidate D novelty.
5. BatchBoot attacks polynomial-multiplication, FFT, and packing costs through a different batched TFHE mechanism. It is a mandatory complete-system baseline, not evidence for Candidate D by itself.
6. Candidate D and BatchBoot may be complementary. That is an experimental
   hypothesis requiring same-backend B2 reproduction or a composed path.
7. The only admissible distinct endpoint is complete
   `T_bootstrap/(r*N_active)`, with standard-object, noise, resource, and B1/B2
   gates. Kernel-only or ciphertext-format-only gains are insufficient.
8. The reviewed 2025/686 anchors bind the binary SAB schedule, amortized complexity, security accounting, and failure target. They do not prove the proposed late-binding operator.

## Routing

Keep Candidate D at `D0_BASELINE_FROZEN` until the atomic Task 9 admission controller records `BLOCK_CANDIDATE_D_INCOMPLETE_EVIDENCE`. Tasks D2-D8 are skipped for this run. The finite resume condition is a locally hash-bound, page-anchored review of every source listed above as missing; repeated network probing is not part of the loop.

This result is not a Candidate D rejection on mathematical grounds and is not a bootstrapping speedup claim. It is a reproducible evidence-bound stop decision.
