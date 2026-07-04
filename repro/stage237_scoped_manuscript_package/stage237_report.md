# Stage237 Scoped Manuscript Package

Decision: `PASS_STAGE237_SCOPED_MANUSCRIPT_PACKAGE_READY_CLAIM_BOUNDED`.

Stage237 turns the selected binary high-stat matrix into a bounded manuscript
and engineering-report package. The package keeps the original algorithmic
object: exact dense PVW/MAT-SAB as an r-body MAT-RLWE/SAB accumulator, measured
by complete-SAB `T_bootstrap/r`. It does not turn the evidence into a
theoretical-optimality, all-parameter, compact-route, or broad novelty claim.

## Selected Binary Experiment Table

| param | r | stage | stat_level | mean_speedup | speedup_ci95_low | speedup_ci95_high | noise_failures | key_bytes_ratio | keygen_ratio | rss_ratio | status | evidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SET_4_5_2048 | 4 | Stage233 | high-stat n=10/seeds=20 | 1.357500 | 1.344091 | 1.370909 | 0/0/0 | 1.069425 | 1.338877 | 1.000880 | PASS_HIGHSTAT_SLICE | repro/stage233_set_4_5_2048_r4_highstat_slice/proof_gate.csv |
| SET_4_5_2048 | 2 | Stage234 | high-stat n=10/seeds=20 | 1.264700 | 1.255514 | 1.273886 | 0/0/0 | 1.014389 | 1.262692 | 0.991062 | PASS_HIGHSTAT_SLICE | repro/stage234_set_4_5_2048_r2_highstat_slice/proof_gate.csv |
| SET_2_3_4096 | 2 | Stage235 | high-stat n=10/seeds=20 | 1.256900 | 1.229193 | 1.284607 | 0/0/0 | 1.006136 | 1.102149 | 0.982190 | PASS_HIGHSTAT_SLICE | repro/stage235_set_2_3_4096_r2_highstat_slice/proof_gate.csv |
| SET_2_3_4096 | 4 | Stage236 | high-stat n=10/seeds=20 | 1.329600 | 1.317739 | 1.341461 | 0/0/0 | 1.031844 | 1.357920 | 0.968173 | PASS_HIGHSTAT_SLICE | repro/stage236_set_2_3_4096_r4_highstat_slice/proof_gate.csv |

## Contribution Claim Ledger

| claim_id | status | safe_wording | quantitative_support | required_caveat | blocked_wording | evidence |
| --- | --- | --- | --- | --- | --- | --- |
| C1_selected_binary_throughput | ALLOW_SCOPED_REPORT | Exact dense PVW/MAT-SAB improves complete-SAB T_bootstrap/r over repeated scalar SAB on the selected binary rows. | mean speedups 1.357500, 1.264700, 1.256900, 1.329600; weakest CI lower bound 1.229193 | Report parameter, r, backend, run count, seed count, key bytes, keygen, RSS, and commit/proof gate. | Do not claim all-parameter speedup, non-binary support, novelty, or theoretical optimality. | repro/stage236_set_2_3_4096_r4_highstat_slice/selected_binary_matrix_summary.csv |
| C2_correctness_noise_side_condition | ALLOW_SCOPED_REPORT | The four selected binary rows have zero PVW/scalar/pair final-output failures under 20 deterministic seeds each. | all rows record noise_failures 0/0/0 | This is sampled final-output noise/correctness evidence, not a full proof of every parameter branch. | Do not use sampled noise evidence as a universal correctness theorem. | repro/stage236_set_2_3_4096_r4_highstat_slice/selected_binary_matrix_summary.csv |
| C3_resource_side_costs | ALLOW_SCOPED_REPORT | Throughput gains are reported with key-size, keygen, and RSS side costs. | key bytes ratio range 1.006136..1.069425; keygen ratio range 1.102149..1.357920; RSS ratio range 0.968173..1.000880 | Do not hide slower keygen or public-key growth when reporting speedups. | Do not report throughput alone as final efficiency. | repro/stage236_set_2_3_4096_r4_highstat_slice/selected_binary_matrix_summary.csv |
| C4_novelty | SCOPED_ONLY_NOT_FINAL | The current draft can describe a scoped systems/engineering study of PVW/MAT-SAB for 2025/686-style SAB. | Stage230 allows only scoped systems wording and rejects broad shared-mask/PVW/external-product novelty. | Cite related-work axes and avoid first/new language unless a later citation audit upgrades the claim. | Do not claim first shared-mask batching, first PVW packing, or first TFHE external product. | repro/stage230_source_verified_literature_novelty_audit/novelty_risk_map.csv |
| C5_optimality | DENY | The current complexity model identifies measured lower-bound-style constraints and candidate paths, but no formal optimality theorem is complete. | none | State theoretical optimality as future work. | Do not state theoretically optimal, universally optimal, or lower-bound tight. | repro/stage227_exact_route_claim_boundary_update/claim_matrix.csv |

## Section Evidence Matrix

| section | content_scope | must_include | evidence |
| --- | --- | --- | --- |
| Abstract | One-paragraph summary with selected-binary T_bootstrap/r results and explicit claim boundary. | four-row speedup range, same-backend repeated scalar baseline, non-binary/optimality caveat | repro/stage237_scoped_manuscript_package/contribution_claims.csv |
| Introduction | Motivate r-body MAT-RLWE ciphertexts for SAB lanes and define T_bootstrap/r as the endpoint. | why scalar repeated SAB is the baseline and why isolated MAT-EP speed is insufficient | repro/stage227_exact_route_claim_boundary_update/metric_ledger.csv |
| Background and Related Work | Use source-verified axes for 2025/686 SAB, incomplete NTT, common-mask TFHE, batch/SIMD bootstrapping, PVW packing, and TFHE external product. | source status and novelty risk labels | repro/stage230_source_verified_literature_novelty_audit/related_work_axes.csv |
| Algorithm Object | Define exact dense PVW/MAT-SAB as shared-mask r-body accumulator over the existing SAB schedule. | scalar SAB unchanged; sab_pvw path explicit; r means independent LUT/SAB lanes | repro/stage236_set_2_3_4096_r4_highstat_slice/proof_gate.csv |
| Complexity and Candidate Paths | Report cost model, dense MAT arithmetic pressure, and candidate routes with pass/blocked status. | no formal optimality theorem; current optimum is empirical among tested routes | repro/stage237_scoped_manuscript_package/candidate_path_matrix.csv |
| Implementation | Describe current exact dense path, active-buffer fusion, AVX512 specialization, and explicit flags. | same backend and run conditions | repro/stage236_set_2_3_4096_r4_highstat_slice/stage236_report.md |
| Evaluation | Report the selected binary matrix table, noise, resource, and reproducibility commands. | mean, CI, failure counts, key/RSS/keygen ratios | repro/stage237_scoped_manuscript_package/experiment_table_selected_binary.csv |
| Limitations | State blocked claims and remaining gates. | non-binary, compact route, all-parameter scope, novelty, theoretical optimality | repro/stage237_scoped_manuscript_package/overclaim_guard.csv |

## Source Policy

| source_id | title | verification_status | allowed_use | required_caveat | primary_url |
| --- | --- | --- | --- | --- | --- |
| FAB686_2025 | Fast amortized bootstrapping with small keys and polynomial noise overhead | VERIFIED_PRIMARY_OR_OFFICIAL_METADATA | Target baseline; our work must be framed as PVW/MAT-SAB on top of this schedule. | Use as source-verified related-work/metadata evidence; do not fabricate theorem-level claims not checked in the source. | https://eprint.iacr.org/2025/686 |
| INCNTT25_696 | Faster amortized bootstrapping using the incomplete NTT for free | VERIFIED_PRIMARY_OR_OFFICIAL_METADATA | Direct adjacent post-686 acceleration; backend/transform gains must be separated from PVW/MAT lane batching. | Use as source-verified related-work/metadata evidence; do not fabricate theorem-level claims not checked in the source. | https://eprint.iacr.org/2025/696 |
| SHAREMASK25_2112 | Sharing the Mask: TFHE Bootstrapping on Packed Messages | VERIFIED_OFFICIAL_METADATA | Strong prior-art risk for broad shared-mask/common-mask and packed-message novelty claims. | Use as source-verified related-work/metadata evidence; do not fabricate theorem-level claims not checked in the source. | https://doi.org/10.46586/tches.v2025.i4.925-971 |
| BATCHBOOT26 | BatchBoot: Fast Batched Bootstrapping for TFHE scheme and Practical Applications | VERIFIED_OFFICIAL_METADATA | Systems-level batched TFHE work; broad batched bootstrapping novelty is blocked. | Use as source-verified related-work/metadata evidence; do not fabricate theorem-level claims not checked in the source. | https://www.usenix.org/conference/usenixsecurity26/presentation/li-zhihao |
| LW23A_B | Batch Bootstrapping I/II | VERIFIED_OFFICIAL_METADATA | Batch/SIMD bootstrapping framework prior art; blocks broad amortized/SIMD novelty. | Use as source-verified related-work/metadata evidence; do not fabricate theorem-level claims not checked in the source. | https://dl.acm.org/doi/10.1007/978-3-031-30620-4_11 |
| BGH2012_565 | Packed Ciphertexts in LWE-based Homomorphic Encryption | VERIFIED_PRIMARY_OR_OFFICIAL_METADATA | PVW/LWE packing background; PVW packing itself is not novel. | Use as source-verified related-work/metadata evidence; do not fabricate theorem-level claims not checked in the source. | https://eprint.iacr.org/2012/565 |
| CGGI2018_421 | TFHE: Fast Fully Homomorphic Encryption over the Torus | VERIFIED_PRIMARY_OR_OFFICIAL_METADATA | TFHE and external-product background; our external-product use must be scoped to MAT/PVW-SAB integration. | Use as source-verified related-work/metadata evidence; do not fabricate theorem-level claims not checked in the source. | https://eprint.iacr.org/2018/421 |
| MS2018_532 | Ring Packing and Amortized FHEW Bootstrapping | VERIFIED_PRIMARY_OR_OFFICIAL_METADATA | Foundational amortized FHEW line; amortization over many bits is established prior art. | Use as source-verified related-work/metadata evidence; do not fabricate theorem-level claims not checked in the source. | https://eprint.iacr.org/2018/532 |
| GPVL2023_014 | Amortized Bootstrapping Revisited: Simpler, Asymptotically-faster, Implemented | VERIFIED_PRIMARY_OR_OFFICIAL_METADATA | Lineage for practical amortized bootstrapping; our claim must focus on 2025/686 PVW/MAT implementation. | Use as source-verified related-work/metadata evidence; do not fabricate theorem-level claims not checked in the source. | https://eprint.iacr.org/2023/014 |
| DKMS2024_112 | Faster Amortized FHEW Bootstrapping Using Ring Automorphisms | VERIFIED_PRIMARY_OR_OFFICIAL_METADATA | Adjacent amortized acceleration via automorphisms; blocks broad acceleration novelty. | Use as source-verified related-work/metadata evidence; do not fabricate theorem-level claims not checked in the source. | https://eprint.iacr.org/2023/112 |
| LW2023_910 | Amortized Functional Bootstrapping in less than 7ms, with O(1) polynomial multiplications | VERIFIED_PRIMARY_OR_OFFICIAL_METADATA | Adjacent amortized functional bootstrapping; performance wording must be context-specific. | Use as source-verified related-work/metadata evidence; do not fabricate theorem-level claims not checked in the source. | https://eprint.iacr.org/2023/910 |

## Candidate Path Matrix

| path_id | algorithm_path | theory_status | experiment_status | expected_bottleneck | promotion_rule | evidence |
| --- | --- | --- | --- | --- | --- | --- |
| P1_exact_dense_pvw_mat_sab | Exact dense MAT/PVW r-body SAB with shared mask and independent body lanes. | closed for tested semantics; no formal optimality theorem | selected binary high-stat complete | dense MAT external product and SAB schedule body work | already promoted for selected binary rows only | repro/stage236_set_2_3_4096_r4_highstat_slice/selected_binary_matrix_summary.csv |
| P2_native_counter_backend_validation | Use native counters/backend attribution to separate implementation effects from algorithmic lane batching. | mechanism attribution only | optional after Stage237 | cycles/load/store around MAT external product and DFT conversion | must improve or explain complete-SAB T_bootstrap/r; otherwise attribution only | repro/stage226_exact_mat_avx_counter_attribution/attribution_summary.csv |
| P3_compact_or_sparse_selector_mat | Exploit SAB selector structure to reduce dense MAT work or key material. | blocked by selector/security/noise proof obligations | not complete-SAB admitted | encrypted selector indistinguishability and closed shared-mask equations | closed equations, production keygen, isolated equivalence, noise proof, full SAB A/B | repro/stage236_set_2_3_4096_r4_highstat_slice/next_stage_queue.csv |
| P4_nonbinary_pvw_sab | Extend exact MAT/PVW-SAB beyond binary branches. | unsupported in current claim | blocked | branch-specific selector and noise behavior | branch-specific correctness/noise/resource/full-SAB A/B | repro/stage236_set_2_3_4096_r4_highstat_slice/proof_gate.csv |
| P5_theoretical_optimality | Prove a lower-bound-tight r-body MAT-RLWE SAB construction. | open | not applicable | formal model must account for encrypted selectors, dense external product, and output lanes | new theorem with assumptions, proof, and relation to prior art | repro/stage227_exact_route_claim_boundary_update/claim_matrix.csv |

## Overclaim Guard

| phrase | count | status | allowed_context |
| --- | --- | --- | --- |
| first shared-mask | 3 | PASS_CONTEXTUAL_GUARD | allowed if only present in blocked wording or limitations |
| first pvw packing | 3 | PASS_CONTEXTUAL_GUARD | allowed if only present in blocked wording or limitations |
| first external product | 1 | PASS_CONTEXTUAL_GUARD | allowed if only present in blocked wording or limitations |
| all-parameter speedup | 2 | PASS_CONTEXTUAL_GUARD | allowed if only present in blocked wording or limitations |
| non-binary support | 4 | PASS_CONTEXTUAL_GUARD | allowed if only present in blocked wording or limitations |
| theoretically optimal | 2 | PASS_CONTEXTUAL_GUARD | allowed if only present in blocked wording or limitations |
| universally optimal | 2 | PASS_CONTEXTUAL_GUARD | allowed if only present in blocked wording or limitations |
| lower-bound tight | 2 | PASS_CONTEXTUAL_GUARD | allowed if only present in blocked wording or limitations |
| compact selector construction succeeds | 0 | PASS_ABSENT | allowed if only present in blocked wording or limitations |

## Gates

| gate | required | observed | status | claim_effect |
| --- | --- | --- | --- | --- |
| G1_inputs | Stage236 matrix, Stage230 source policy, Stage227 claim boundary, Stage226 attribution exist | all present | PASS | allows manuscript package refresh |
| G2_matrix | four selected binary rows have high-stat performance/noise/resource evidence | four rows pass | PASS_SELECTED_BINARY_MATRIX | allows selected-binary performance table only |
| G3_primary_metric | primary endpoint is complete-SAB T_bootstrap/r | metric fixed in claims and manuscript | PASS | prevents isolated-kernel speedup overclaim |
| G4_source_policy | source rows are taken from Stage230 verified primary/official metadata matrix | 11 source rows | PASS | keeps references source-grounded |
| G5_optimality_boundary | theoretical optimality remains denied | C5_optimality DENY | BOUNDARY_HELD | blocks theoretical-optimality wording |
| G6_overclaim_scan | forbidden phrases absent or contextualized as blocked wording/limitations | contextual guard pass | PASS_CONTEXTUAL_GUARD | prevents manuscript overclaim |
| G7_stage237_decision | all report package gates pass | PASS_STAGE237_SCOPED_MANUSCRIPT_PACKAGE_READY_CLAIM_BOUNDED | PASS_STAGE237_SCOPED_MANUSCRIPT_PACKAGE_READY_CLAIM_BOUNDED | move to source/citation finalization or native-counter attribution |

## Proof Gates

| gate | status | metric | value | evidence | interpretation |
| --- | --- | --- | --- | --- | --- |
| G1_inputs | PASS | Stage236 matrix, Stage230 source policy, Stage227 claim boundary, Stage226 attribution exist | all present | repro/stage237_scoped_manuscript_package/gate_matrix.csv | allows manuscript package refresh |
| G2_matrix | PASS_SELECTED_BINARY_MATRIX | four selected binary rows have high-stat performance/noise/resource evidence | four rows pass | repro/stage237_scoped_manuscript_package/gate_matrix.csv | allows selected-binary performance table only |
| G3_primary_metric | PASS | primary endpoint is complete-SAB T_bootstrap/r | metric fixed in claims and manuscript | repro/stage237_scoped_manuscript_package/gate_matrix.csv | prevents isolated-kernel speedup overclaim |
| G4_source_policy | PASS | source rows are taken from Stage230 verified primary/official metadata matrix | 11 source rows | repro/stage237_scoped_manuscript_package/gate_matrix.csv | keeps references source-grounded |
| G5_optimality_boundary | BOUNDARY_HELD | theoretical optimality remains denied | C5_optimality DENY | repro/stage237_scoped_manuscript_package/gate_matrix.csv | blocks theoretical-optimality wording |
| G6_overclaim_scan | PASS_CONTEXTUAL_GUARD | forbidden phrases absent or contextualized as blocked wording/limitations | contextual guard pass | repro/stage237_scoped_manuscript_package/gate_matrix.csv | prevents manuscript overclaim |
| G7_stage237_decision | PASS_STAGE237_SCOPED_MANUSCRIPT_PACKAGE_READY_CLAIM_BOUNDED | all report package gates pass | PASS_STAGE237_SCOPED_MANUSCRIPT_PACKAGE_READY_CLAIM_BOUNDED | repro/stage237_scoped_manuscript_package/gate_matrix.csv | move to source/citation finalization or native-counter attribution |

## Next Queue

| priority | route | entry_condition | gate | status | failure_action | evidence |
| --- | --- | --- | --- | --- | --- | --- |
| P0 | stage238_source_verified_citation_package | Scoped manuscript package is ready and a paper-facing draft needs citation-precise statements. | Every related-work and background sentence must map to a Stage230 source row or a freshly verified source. | ready | Keep Stage237 as engineering report, not final paper draft. | repro/stage237_scoped_manuscript_package/source_policy.csv |
| P1 | stage239_native_counter_backend_validation | The draft needs stronger implementation attribution beyond complete-SAB timing. | Native Linux perf counters or explicit WSL proxy label; no theoretical-optimality wording. | optional | Omit counter claims and keep only timing/resource/noise evidence. | repro/stage237_scoped_manuscript_package/candidate_path_matrix.csv |
| P2 | stage240_nonbinary_or_compact_design | The research target expands beyond exact dense binary PVW/MAT-SAB. | Closed selector equations, security/noise model, production keygen, isolated equivalence, and full SAB A/B. | blocked_until_design | Do not claim non-binary, compact, or theoretical-optimal MAT-RLWE SAB. | repro/stage237_scoped_manuscript_package/contribution_claims.csv |

## Inputs

| input | status | role | bytes |
| --- | --- | --- | --- |
| repro/stage236_set_2_3_4096_r4_highstat_slice/proof_gate.csv | present | Stage236 selected binary matrix proof | 2238 |
| repro/stage236_set_2_3_4096_r4_highstat_slice/selected_binary_matrix_summary.csv | present | Stage236 four-row selected binary experiment table | 899 |
| repro/stage236_set_2_3_4096_r4_highstat_slice/stage236_report.md | present | Stage236 report with metric and boundary | 16890 |
| repro/stage230_source_verified_literature_novelty_audit/source_verification_refresh.csv | present | Stage230 source verification refresh | 3734 |
| repro/stage230_source_verified_literature_novelty_audit/novelty_risk_map.csv | present | Stage230 novelty risk map | 1469 |
| repro/stage230_source_verified_literature_novelty_audit/claim_policy.csv | present | Stage230 claim policy | 824 |
| repro/stage230_source_verified_literature_novelty_audit/related_work_axes.csv | present | Stage230 related-work axes | 1021 |
| repro/stage227_exact_route_claim_boundary_update/claim_matrix.csv | present | Stage227 metric/claim boundary | 2129 |
| repro/stage227_exact_route_claim_boundary_update/metric_ledger.csv | present | Stage227 T_bootstrap/r metric ledger | 2565 |
| repro/stage226_exact_mat_avx_counter_attribution/attribution_summary.csv | present | Stage226 native counter attribution, optional mechanism only | 1607 |
