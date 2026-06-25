# Stage 27 Final Evidence Package

Date: 2026-06-25

## Scope

This package aggregates already-recorded Stage 25/26/27 evidence for the
explicit PVW/MAT-SAB path. It supports a scoped engineering claim only.
It does not support novelty, non-binary PVW-SAB, all-parameter speedup,
or theoretical-optimal AVX512 claims.

Primary endpoint: complete `sab_pvw_*` bootstrapping throughput versus
repeated scalar SAB under the same backend and parameter scope.

## Performance

| scope | param | r | runs | mean_speedup | min_speedup | max_speedup | interpretation |
| --- | --- | --- | --- | --- | --- | --- | --- |
| target_binary_final_rerun | SET_2_3_2048 | 2 | 3 | 1.171 | 1.111 | 1.285 | positive but noisy target evidence |
| target_binary_final_rerun | SET_2_3_2048 | 4 | 3 | 1.401 | 1.331 | 1.472 | strongest current target evidence |
| added_binary_small_sample | SET_2_3_4096 | 2 | 5 | 1.224 | 1.207 | 1.233 | positive small-sample support |
| added_binary_small_sample | SET_2_3_4096 | 4 | 5 | 1.318 | 1.272 | 1.350 | positive small-sample support |
| added_binary_small_sample | SET_4_5_2048 | 2 | 5 | 1.329 | 1.082 | 1.473 | positive mean; high timing variance, report range/CI |
| added_binary_small_sample | SET_4_5_2048 | 4 | 5 | 1.346 | 1.305 | 1.455 | positive small-sample support |

## Final-Output Noise

| scope | param | r | seeds | points | pvw_failures | scalar_failures | pair_failures | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| target_binary_50_seed | SET_2_3_2048 | 2 | 50 | 204800 | 0 | 0 | 0 | PASS |
| target_binary_50_seed | SET_2_3_2048 | 4 | 50 | 409600 | 0 | 0 | 0 | PASS |
| added_binary_5_seed | SET_2_3_4096 | 2 | 5 | 40960 | 0 | 0 | 0 | PASS |
| added_binary_5_seed | SET_2_3_4096 | 4 | 5 | 81920 | 0 | 0 | 0 | PASS |
| added_binary_5_seed | SET_4_5_2048 | 2 | 5 | 20480 | 0 | 0 | 0 | PASS |
| added_binary_5_seed | SET_4_5_2048 | 4 | 5 | 40960 | 0 | 0 | 0 | PASS |

## Resource Snapshot

| r | mode | keygen_lane_avg_us | estimated_key_bytes_ratio_vs_scalar_repeated | time_max_rss_kb |
| --- | --- | --- | --- | --- |
| 2 | pvw | 573741.000 | 1.013617 | 383240 |
| 4 | pvw | 599465.000 | 1.065349 | 769388 |

## Claim Boundary

| claim_id | status_label | manuscript_action | claim |
| --- | --- | --- | --- |
| C1 | SUPPORTED_ENGINEERING | allowed_if_scoped | PVW/MAT-SAB implementation exists beside scalar SAB |
| C2 | SUPPORTED_SCOPED_ENGINEERING | allowed_if_scoped | Complete SAB throughput improves over repeated scalar SAB on tested binary targets |
| C3 | SUPPORTED_TARGET_NOISE | allowed_if_scoped | Current promoted r=2/r=4 target path passes multi-seed final-output noise gates |
| C4 | SUPPORTED_SMALL_SAMPLE | allowed_if_scoped | Added binary parameters have performance/noise support |
| C5 | SUPPORTED_ENGINEERING | allowed_if_scoped | Active-buffer/copyback fusion is a SAB-specific engineering optimization |
| C6 | SUPPORTED_PRACTICAL_NOT_OPTIMAL | allowed_if_scoped | Specialized MAT-AVX512 is useful |
| C7 | BLOCKED_PRIOR_ART_RISK | block_or_limit | Shared-mask or multi-body TFHE batching is novel to this project |
| C8 | BLOCKED_UNSUPPORTED_BRANCH | block_or_limit | PVW-SAB supports ternary/include-zero branches |
| C9 | BLOCKED_DIFFERENT_TECHNIQUE | block_or_limit | Incomplete-NTT work is the same technique as PVW/MAT-SAB |
| C10 | BLOCKED_FULL_TEXT_REQUIRED | block_or_limit | The project is ready for theorem-level 2025/686 citation checks |

## Citation Gate

| gate | status | detail |
| --- | --- | --- |
| direct_pdf_access | BLOCKED | BLOCKED_FULL_TEXT_NOT_AVAILABLE |
| semantic_scholar_metadata | METADATA_AVAILABLE_NO_OPEN_ACCESS_PDF | Fast Amortized Bootstrapping with Small Keys and Polynomial Noise Overhead |
| semantic_scholar_open_access_pdf_url | MISSING |  |
| dblp_title_metadata | TITLE_METADATA_AVAILABLE | hits=2 |
| citation_decision | BLOCK_THEOREM_LEVEL_CITATIONS | Do not cite 2025/686 theorem/algorithm/remark numbers without full text. |

## Completion Readiness

| item_id | category | status | requirement |
| --- | --- | --- | --- |
| F1 | final_standard | SATISFIED_SCOPED | Promoted sab_pvw_* full bootstrapping path matches repeated scalar SAB output under target parameters |
| F2 | final_standard | SATISFIED_SCOPED | Multi-seed correctness/noise gates pass for promoted variants |
| F3 | final_standard | SATISFIED_SCOPED | Complete bootstrapping benchmark evidence shows stable throughput gain over repeated scalar SAB under same backend |
| F4 | final_standard | SATISFIED_SCOPED | Scalar baseline behavior and benchmarkability remain intact |
| F5 | final_standard | SATISFIED_SCOPED | Algorithmic gains and backend/SIMD gains are separated |
| F6 | final_standard | SATISFIED_SMOKE_RESOURCE | Key size, keygen time, memory peak, and scratch/resource overhead are reported |
| F7 | final_standard | SATISFIED_SCOPED | Reproducibility artifacts contain commit, command, backend, CPU flags, logs, summaries, and decisions |
| F8 | final_standard | SATISFIED_FOR_ENGINEERING_BLOCKED_FOR_NOVELTY | Paper-level claims are made only after literature/novelty audit |
| S19 | stage | SATISFIED | Exact sparse schedule audit |
| S20 | stage | SATISFIED_PROMOTED | Active-buffer/copyback fusion implementation and performance gate |
| S21 | stage | SATISFIED_NEUTRAL | sub_a / rotation optimization candidate |
| S22 | stage | SATISFIED_PRACTICAL_NOT_THEORETICAL | MAT-aware AVX512 practical audit |
| S23 | stage | SATISFIED_NEUTRAL | PVW CMUX/NCMUX schedule fusion |
| S24 | stage | SATISFIED_DEFERRED | Conditional post-processing profile |
| S25 | stage | SATISFIED_SCOPED | Correctness/noise/resource matrix |
| S26 | stage | SATISFIED_SCOPED | Parameter and branch generalization |
| S27 | stage | SATISFIED_ENGINEERING_BLOCKED_NOVELTY | Novelty/paper package and final evidence package |

## Decision

```text
FINAL_ENGINEERING_EVIDENCE_PACKAGE_ASSEMBLED
SAFE_SCOPED_ENGINEERING_CLAIM_SUPPORTED
NOVELTY_CLAIM_BLOCKED_PENDING_FULL_2025_686_AND_PRIOR_ART_REVIEW
NON_BINARY_AND_ALL_PARAMETER_CLAIMS_BLOCKED
```

Source CSVs are listed in `repro/stage27_final_evidence_package/manifest.csv`.
