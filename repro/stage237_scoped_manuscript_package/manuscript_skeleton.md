# Scoped Manuscript Skeleton: PVW/MAT-SAB as r-Body SAB

## Abstract Draft

We study an exact dense PVW/MAT-RLWE realization of 2025/686-style sparse
amortized bootstrapping in which one shared mask carries r independent body
lanes. The evaluation endpoint is complete bootstrapping time per processed
plaintext lane, `T_bootstrap/r`, compared against r repeated scalar SAB
executions under the same backend. On the selected binary parameter rows
`SET_4_5_2048` and `SET_2_3_4096`, r=2 and r=4, the current implementation
records mean speedups from `1.256900x..1.357500x` with zero PVW/scalar/pair
final-output failures in 20 deterministic seeds per row. The result is a
scoped systems result: it does not prove non-binary support, compact selector
construction, broad novelty, or theoretical optimality.

## 1. Introduction

The original research question is not whether one external-product kernel can
be faster in isolation. The question is whether changing the SAB accumulator
from r independent RLWE executions to a MAT-RLWE/r-body object improves the
amortized full bootstrapping cost per handled plaintext lane. This draft uses
`T_bootstrap/r` as the primary metric throughout.

## 2. Background and Related Work

The related-work section must be written from the Stage230 source policy. It
should cover the 2025/686 SAB baseline, post-686 incomplete-NTT acceleration,
common-mask packed-message TFHE, batch/SIMD bootstrapping, PVW packing, and
TFHE external products. The draft may position this project as a scoped
PVW/MAT-SAB integration and evaluation. It must not claim first shared-mask
batching, first PVW packing, or first external product.

## 3. Algorithm Object

The implemented algorithm is exact dense PVW/MAT-SAB. The scalar SAB path stays
as the reference path. The PVW path uses a shared mask and r body lanes; here r
means independent LUT/SAB lanes, not accumulator-index packing. Each lane must
match the scalar SAB output for the corresponding input and LUT.

## 4. Complexity and Candidate Paths

The scalar baseline repeats the SAB computation r times. The exact PVW/MAT
path amortizes shared schedule and mask work, but it pays dense MAT external
product costs and resource side costs. The current evidence identifies the
exact dense path as the best promoted route for the selected binary rows. The
candidate path matrix keeps backend-counter attribution, compact/sparse
selector MAT, non-binary support, and theoretical optimality as separate gates.

## 5. Implementation

The report should describe `sab_pvw_*`, active-buffer fusion,
`MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true`, and `spqlios_avx512`. All
performance claims are same-backend complete-SAB comparisons against repeated
scalar SAB, not comparisons against Windows/FFNT or isolated MAT microbenchmarks.

## 6. Evaluation

Primary table:

| param | r | stage | stat_level | mean_speedup | speedup_ci95_low | speedup_ci95_high | noise_failures | key_bytes_ratio | keygen_ratio | rss_ratio | status | evidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SET_4_5_2048 | 4 | Stage233 | high-stat n=10/seeds=20 | 1.357500 | 1.344091 | 1.370909 | 0/0/0 | 1.069425 | 1.338877 | 1.000880 | PASS_HIGHSTAT_SLICE | repro/stage233_set_4_5_2048_r4_highstat_slice/proof_gate.csv |
| SET_4_5_2048 | 2 | Stage234 | high-stat n=10/seeds=20 | 1.264700 | 1.255514 | 1.273886 | 0/0/0 | 1.014389 | 1.262692 | 0.991062 | PASS_HIGHSTAT_SLICE | repro/stage234_set_4_5_2048_r2_highstat_slice/proof_gate.csv |
| SET_2_3_4096 | 2 | Stage235 | high-stat n=10/seeds=20 | 1.256900 | 1.229193 | 1.284607 | 0/0/0 | 1.006136 | 1.102149 | 0.982190 | PASS_HIGHSTAT_SLICE | repro/stage235_set_2_3_4096_r2_highstat_slice/proof_gate.csv |
| SET_2_3_4096 | 4 | Stage236 | high-stat n=10/seeds=20 | 1.329600 | 1.317739 | 1.341461 | 0/0/0 | 1.031844 | 1.357920 | 0.968173 | PASS_HIGHSTAT_SLICE | repro/stage236_set_2_3_4096_r4_highstat_slice/proof_gate.csv |

Every row uses 10 complete-SAB A/B timing samples and 20 deterministic noise
seeds. Resource costs are reported beside throughput.

## 7. Claim Ledger

| claim_id | status | safe_wording | quantitative_support | required_caveat | blocked_wording | evidence |
| --- | --- | --- | --- | --- | --- | --- |
| C1_selected_binary_throughput | ALLOW_SCOPED_REPORT | Exact dense PVW/MAT-SAB improves complete-SAB T_bootstrap/r over repeated scalar SAB on the selected binary rows. | mean speedups 1.357500, 1.264700, 1.256900, 1.329600; weakest CI lower bound 1.229193 | Report parameter, r, backend, run count, seed count, key bytes, keygen, RSS, and commit/proof gate. | Do not claim all-parameter speedup, non-binary support, novelty, or theoretical optimality. | repro/stage236_set_2_3_4096_r4_highstat_slice/selected_binary_matrix_summary.csv |
| C2_correctness_noise_side_condition | ALLOW_SCOPED_REPORT | The four selected binary rows have zero PVW/scalar/pair final-output failures under 20 deterministic seeds each. | all rows record noise_failures 0/0/0 | This is sampled final-output noise/correctness evidence, not a full proof of every parameter branch. | Do not use sampled noise evidence as a universal correctness theorem. | repro/stage236_set_2_3_4096_r4_highstat_slice/selected_binary_matrix_summary.csv |
| C3_resource_side_costs | ALLOW_SCOPED_REPORT | Throughput gains are reported with key-size, keygen, and RSS side costs. | key bytes ratio range 1.006136..1.069425; keygen ratio range 1.102149..1.357920; RSS ratio range 0.968173..1.000880 | Do not hide slower keygen or public-key growth when reporting speedups. | Do not report throughput alone as final efficiency. | repro/stage236_set_2_3_4096_r4_highstat_slice/selected_binary_matrix_summary.csv |
| C4_novelty | SCOPED_ONLY_NOT_FINAL | The current draft can describe a scoped systems/engineering study of PVW/MAT-SAB for 2025/686-style SAB. | Stage230 allows only scoped systems wording and rejects broad shared-mask/PVW/external-product novelty. | Cite related-work axes and avoid first/new language unless a later citation audit upgrades the claim. | Do not claim first shared-mask batching, first PVW packing, or first TFHE external product. | repro/stage230_source_verified_literature_novelty_audit/novelty_risk_map.csv |
| C5_optimality | DENY | The current complexity model identifies measured lower-bound-style constraints and candidate paths, but no formal optimality theorem is complete. | none | State theoretical optimality as future work. | Do not state theoretically optimal, universally optimal, or lower-bound tight. | repro/stage227_exact_route_claim_boundary_update/claim_matrix.csv |

## 8. Candidate Paths

| path_id | algorithm_path | theory_status | experiment_status | expected_bottleneck | promotion_rule | evidence |
| --- | --- | --- | --- | --- | --- | --- |
| P1_exact_dense_pvw_mat_sab | Exact dense MAT/PVW r-body SAB with shared mask and independent body lanes. | closed for tested semantics; no formal optimality theorem | selected binary high-stat complete | dense MAT external product and SAB schedule body work | already promoted for selected binary rows only | repro/stage236_set_2_3_4096_r4_highstat_slice/selected_binary_matrix_summary.csv |
| P2_native_counter_backend_validation | Use native counters/backend attribution to separate implementation effects from algorithmic lane batching. | mechanism attribution only | optional after Stage237 | cycles/load/store around MAT external product and DFT conversion | must improve or explain complete-SAB T_bootstrap/r; otherwise attribution only | repro/stage226_exact_mat_avx_counter_attribution/attribution_summary.csv |
| P3_compact_or_sparse_selector_mat | Exploit SAB selector structure to reduce dense MAT work or key material. | blocked by selector/security/noise proof obligations | not complete-SAB admitted | encrypted selector indistinguishability and closed shared-mask equations | closed equations, production keygen, isolated equivalence, noise proof, full SAB A/B | repro/stage236_set_2_3_4096_r4_highstat_slice/next_stage_queue.csv |
| P4_nonbinary_pvw_sab | Extend exact MAT/PVW-SAB beyond binary branches. | unsupported in current claim | blocked | branch-specific selector and noise behavior | branch-specific correctness/noise/resource/full-SAB A/B | repro/stage236_set_2_3_4096_r4_highstat_slice/proof_gate.csv |
| P5_theoretical_optimality | Prove a lower-bound-tight r-body MAT-RLWE SAB construction. | open | not applicable | formal model must account for encrypted selectors, dense external product, and output lanes | new theorem with assumptions, proof, and relation to prior art | repro/stage227_exact_route_claim_boundary_update/claim_matrix.csv |

## 9. Limitations

This package is not a final paper claim. It is a bounded manuscript skeleton
and evidence map. A final submission still needs source-level citation
verification, a venue/template pass, and a decision on whether to add native
counter attribution or keep it as future work.
