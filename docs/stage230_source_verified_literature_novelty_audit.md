# Stage230 Source-Verified Literature Novelty Audit

Decision: `PASS_STAGE230_SOURCE_VERIFIED_SCOPED_NOVELTY_BOUNDARY`.

Stage230 refreshes the novelty boundary for the PVW/MAT-SAB goal. It uses
real primary or official metadata sources and keeps the contribution scoped:
complete-SAB `T_bootstrap/r` engineering evidence is allowed; broad novelty,
all-parameter, non-binary, and theoretical-optimality claims are not allowed.

## Search Queries

| axis | query | purpose |
| --- | --- | --- |
| target_baseline | IACR ePrint 2025/686 Fast amortized bootstrapping with small keys and polynomial noise overhead | Verify target 2025/686 identity and source route. |
| post_686_transform | IACR ePrint 2025/696 Faster amortized bootstrapping using the incomplete NTT for free | Find direct post-686 amortized bootstrapping acceleration work. |
| common_mask | Sharing the Mask TFHE bootstrapping on Packed Messages TCHES 2025 common mask | Check shared/common-mask packed-message prior art. |
| batch_systems | BatchBoot Fast Batched Bootstrapping for TFHE Scheme USENIX Security 2026 | Check later systems-level batched TFHE work. |
| simd_batch_bootstrapping | Batch Bootstrapping I SIMD bootstrapping polynomial modulus EUROCRYPT 2023 | Check batch/SIMD bootstrapping prior art. |
| packing_background | Packed Ciphertexts in LWE-based Homomorphic Encryption ePrint 2012/565 PVW | Check PVW/LWE packing background. |
| external_product_background | TFHE Fast Fully Homomorphic Encryption over the Torus ePrint 2018/421 external product | Check TFHE/external-product background. |

## Source Verification Refresh

| source_id | title | venue_year | primary_url | secondary_url | verification_status | novelty_impact |
| --- | --- | --- | --- | --- | --- | --- |
| FAB686_2025 | Fast amortized bootstrapping with small keys and polynomial noise overhead | IACR ePrint 2025/686; ACM CCS 2025 metadata | https://eprint.iacr.org/2025/686 | https://github.com/antoniocgj/Fast-Amortized-Bootstrapping | VERIFIED_PRIMARY_OR_OFFICIAL_METADATA | Target baseline; our work must be framed as PVW/MAT-SAB on top of this schedule. |
| INCNTT25_696 | Faster amortized bootstrapping using the incomplete NTT for free | IACR ePrint 2025/696 | https://eprint.iacr.org/2025/696 | https://github.com/thalespaiva/incomplete_ntt_amortized_bt | VERIFIED_PRIMARY_OR_OFFICIAL_METADATA | Direct adjacent post-686 acceleration; backend/transform gains must be separated from PVW/MAT lane batching. |
| SHAREMASK25_2112 | Sharing the Mask: TFHE Bootstrapping on Packed Messages | TCHES 2025(4):925-971 metadata | https://doi.org/10.46586/tches.v2025.i4.925-971 | https://dblp.org/rec/journals/tches/BergeratBCOPT25 | VERIFIED_OFFICIAL_METADATA | Strong prior-art risk for broad shared-mask/common-mask and packed-message novelty claims. |
| BATCHBOOT26 | BatchBoot: Fast Batched Bootstrapping for TFHE scheme and Practical Applications | USENIX Security 2026 accepted/prepub metadata | https://www.usenix.org/conference/usenixsecurity26/presentation/li-zhihao | https://www.usenix.org/system/files/conference/usenixsecurity26/sec26_prepub_li-zhihao.pdf | VERIFIED_OFFICIAL_METADATA | Systems-level batched TFHE work; broad batched bootstrapping novelty is blocked. |
| LW23A_B | Batch Bootstrapping I/II | EUROCRYPT 2023 | https://dl.acm.org/doi/10.1007/978-3-031-30620-4_11 | https://dl.acm.org/doi/10.1007/978-3-031-30620-4_12 | VERIFIED_OFFICIAL_METADATA | Batch/SIMD bootstrapping framework prior art; blocks broad amortized/SIMD novelty. |
| BGH2012_565 | Packed Ciphertexts in LWE-based Homomorphic Encryption | IACR ePrint 2012/565; PKC 2013 metadata | https://eprint.iacr.org/2012/565 | https://dblp.org/rec/journals/iacr/BrakerskiGH12 | VERIFIED_PRIMARY_OR_OFFICIAL_METADATA | PVW/LWE packing background; PVW packing itself is not novel. |
| CGGI2018_421 | TFHE: Fast Fully Homomorphic Encryption over the Torus | IACR ePrint 2018/421; Journal of Cryptology 2019 | https://eprint.iacr.org/2018/421 | https://dl.acm.org/doi/10.1007/s00145-019-09319-x | VERIFIED_PRIMARY_OR_OFFICIAL_METADATA | TFHE and external-product background; our external-product use must be scoped to MAT/PVW-SAB integration. |
| MS2018_532 | Ring Packing and Amortized FHEW Bootstrapping | ICALP 2018; IACR ePrint 2018/532 | https://eprint.iacr.org/2018/532 | https://drops.dagstuhl.de/entities/document/10.4230/LIPIcs.ICALP.2018.100 | VERIFIED_PRIMARY_OR_OFFICIAL_METADATA | Foundational amortized FHEW line; amortization over many bits is established prior art. |
| GPVL2023_014 | Amortized Bootstrapping Revisited: Simpler, Asymptotically-faster, Implemented | IACR ePrint 2023/014; ASIACRYPT 2023 | https://eprint.iacr.org/2023/014 | https://dblp.org/rec/conf/asiacrypt/GuimaraesPL23 | VERIFIED_PRIMARY_OR_OFFICIAL_METADATA | Lineage for practical amortized bootstrapping; our claim must focus on 2025/686 PVW/MAT implementation. |
| DKMS2024_112 | Faster Amortized FHEW Bootstrapping Using Ring Automorphisms | IACR ePrint 2023/112; PKC 2024 | https://eprint.iacr.org/2023/112 | https://dl.acm.org/doi/10.1007/978-3-031-57728-4_11 | VERIFIED_PRIMARY_OR_OFFICIAL_METADATA | Adjacent amortized acceleration via automorphisms; blocks broad acceleration novelty. |
| LW2023_910 | Amortized Functional Bootstrapping in less than 7ms, with O(1) polynomial multiplications | IACR ePrint 2023/910; ASIACRYPT 2023 | https://eprint.iacr.org/2023/910 | https://dblp.org/rec/conf/asiacrypt/LiuW23 | VERIFIED_PRIMARY_OR_OFFICIAL_METADATA | Adjacent amortized functional bootstrapping; performance wording must be context-specific. |

## Related-Work Axes

| axis | sources | relation | stage230_boundary |
| --- | --- | --- | --- |
| target_sab | FAB686_2025 | Target sparse amortized bootstrapping baseline. | PVW/MAT-SAB is a scoped r-body implementation path over this target, not a replacement theorem. |
| post_686_acceleration | INCNTT25_696 | Direct post-686 transform/backend acceleration. | Separate algorithmic MAT lane batching from NTT/backend improvements. |
| common_mask_packed_tfhe | SHAREMASK25_2112 | Common-mask/shared-mask packed-message TFHE work. | Reject broad shared-mask novelty; allow only 686-specific PVW/MAT-SAB integration wording. |
| batch_simd_bootstrapping | MS2018_532; GPVL2023_014; DKMS2024_112; LW2023_910; LW23A_B; BATCHBOOT26 | Amortized, batch, SIMD, and systems-level bootstrapping prior art. | Report per-lane T_bootstrap/r evidence; do not claim amortization/batching itself is new. |
| packing_external_product_background | BGH2012_565; CGGI2018_421 | PVW/LWE packing and TFHE external-product background. | Do not claim PVW packing or external products as new; claim only local MAT/PVW-SAB adaptation evidence. |

## Novelty Risk Map

| claim | risk | decision | reason | required_writing_caveat |
| --- | --- | --- | --- | --- |
| PVW/MAT-SAB complete bootstrapping improves T_bootstrap/r over repeated scalar SAB on recorded binary settings. | LOW_TO_MEDIUM | ALLOW_SCOPED_SYSTEMS_CLAIM | Local complete-SAB A/B, noise, and resource gates exist, and Stage229 fixes the per-lane metric. | Always report backend, r, parameter, commit/state, runs, CI, and resource side costs. |
| Shared-mask or multi-body TFHE/PVW ciphertext batching is new. | HIGH_PRIOR_ART | REJECT_BROAD_NOVELTY | Sharing the Mask, Batch Bootstrapping, BatchBoot, and amortized FHEW works cover adjacent common-mask/batch/amortized ideas. | Position only the 2025/686 SAB integration and measured local route. |
| The current dense MAT/PVW path is theoretically optimal for r-body SAB. | UNSUPPORTED | REJECT_OPTIMALITY_CLAIM | Stage229 and Stage226 leave dense MAT optimality open; source audit does not supply a lower bound. | Use empirical systems language and list theoretical optimality as future work. |
| PVW packing or TFHE external product is novel. | INVALID | REJECT | BGH2012 and TFHE background sources establish these as prior art. | Cite as background only. |
| The contribution is a scoped empirical study of PVW/MAT r-body external-product batching inside 2025/686 SAB. | MEDIUM | ALLOW_CANDIDATE_WITH_CAVEATS | This is narrower than broad batching/common-mask novelty and matches the implemented evidence chain. | Must cite adjacent work and avoid 'first' language unless a later exhaustive review supports it. |

## Claim Policy

| scope | allowed | forbidden |
| --- | --- | --- |
| paper_title_or_abstract | A systems/engineering study of PVW/MAT r-body batching for 2025/686-style sparse amortized bootstrapping. | A new universally optimal MAT-RLWE SAB algorithm. |
| performance | Complete-SAB `T_bootstrap/r` speedup over repeated scalar SAB under same backend and recorded parameters. | Kernel-only speedup or backend-only speedup described as final bootstrapping acceleration. |
| novelty | Scoped candidate contribution after acknowledging common-mask, batch/SIMD, PVW packing, and amortized bootstrapping prior art. | First shared-mask, first batch bootstrapping, first PVW packing, or first TFHE external-product claim. |
| future work | Non-binary PVW-SAB, all-parameter support, compact selector route, and theoretical optimality remain open gates. | Treating open gates as already completed. |

## Proof Gates

| gate | status | metric | value | evidence | interpretation |
| --- | --- | --- | --- | --- | --- |
| G1_required_inputs | PASS | inputs_present | true | repro/stage230_source_verified_literature_novelty_audit/input_status.csv | Stage230 starts from Stage229 claim boundaries and prior verified matrices. |
| G2_source_verification_refresh | PASS | verified_sources | 11/11 | repro/stage230_source_verified_literature_novelty_audit/source_verification_refresh.csv | All Stage230 rows use primary or official metadata URLs; no fabricated references. |
| G3_related_axes | PASS | axes | 5 | repro/stage230_source_verified_literature_novelty_audit/related_work_axes.csv | The audit is targeted to the PVW/MAT-SAB delta, not a broad FHE survey. |
| G4_novelty_policy | PASS_SCOPED_BOUNDARY | allow_or_reject | allow=2;reject=3 | repro/stage230_source_verified_literature_novelty_audit/novelty_risk_map.csv | Scoped systems claim is allowed; broad novelty and optimality claims are rejected. |
| G5_stage230_decision | PASS_STAGE230_SOURCE_VERIFIED_SCOPED_NOVELTY_BOUNDARY | decision | PASS_STAGE230_SOURCE_VERIFIED_SCOPED_NOVELTY_BOUNDARY | repro/stage230_source_verified_literature_novelty_audit/proof_gate.csv | Proceed to current-head parameter refresh or manuscript skeleton only under the claim policy. |

## Next Queue

| priority | route | entry_condition | gate | status | failure_action | evidence |
| --- | --- | --- | --- | --- | --- | --- |
| P0 | stage231_current_head_added_parameter_refresh | A paper table needs current-head evidence beyond SET_2_3_2048/r6. | Rerun selected added binary parameters at current head with printed shapes, same-backend A/B, noise, and resource. | selected_if_broad_parameter_table_needed | Keep added-parameter rows historical/scoped. | repro/stage230_source_verified_literature_novelty_audit/claim_policy.csv |
| P1 | stage232_scoped_manuscript_skeleton_refresh | User wants a paper/report draft after Stage230 policy. | Every claim must cite a Stage230 source or local repro artifact; no broad novelty language. | future | Return to claim policy and remove unsupported text. | repro/stage230_source_verified_literature_novelty_audit/novelty_risk_map.csv |
| P2 | stage233_nonbinary_or_compact_route_design | User wants to expand algorithm support beyond exact dense binary PVW/MAT-SAB. | Selector/key equations, security/noise, isolated equivalence, then full SAB A/B. | blocked_until_design | Do not claim non-binary, compact, or optimal MAT-RLWE SAB. | repro/stage230_source_verified_literature_novelty_audit/claim_policy.csv |

## Inputs

| input | status | role | bytes |
| --- | --- | --- | --- |
| repro/stage229_parameter_generalization_matrix/proof_gate.csv | present | Stage229 proof gate | 1675 |
| repro/stage229_parameter_generalization_matrix/next_stage_queue.csv | present | Stage229 next queue selecting source-verified novelty audit | 1061 |
| repro/stage229_parameter_generalization_matrix/claim_scope.csv | present | Stage229 scoped claim policy | 1783 |
| repro/stage103_related_work_novelty_review/source_verification.csv | present | Prior source verification matrix | 3140 |
| repro/stage103_related_work_novelty_review/related_work_matrix.csv | present | Prior related-work axes | 1159 |
| repro/stage103_related_work_novelty_review/novelty_claim_matrix.csv | present | Prior novelty claim policy | 2072 |
| docs/stage177_verified_literature_novelty_gate.md | present | Prior bounded literature novelty gate | 13444 |
| docs/stage204_source_anchor_intake.md | present | Source anchor intake and metadata boundaries | 9329 |
| stage229_next_selects_stage230 | present | Keeps literature work on the registered P0 route. |  |
