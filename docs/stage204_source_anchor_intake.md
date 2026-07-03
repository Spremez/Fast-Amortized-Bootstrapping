# Stage204 Source Anchor Intake

Decision: `PASS_STAGE204_SOURCE_ANCHOR_INTAKE_METADATA_ONLY`.

Stage204 converts the source-anchor blocker into a bounded evidence record. It
uses real public source URLs for metadata, implementation-environment policy,
and experiment planning. It does not claim coverage of theorem-level content.

## Summary

| gate | status | metric | value | evidence | detail | next_action |
| --- | --- | --- | --- | --- | --- | --- |
| stage204_inputs | PASS | required_stage203_inputs_present | 1 | repro/stage203_production_selector_equation_probe/summary.csv; repro/stage203_production_selector_equation_probe/proof_gate.csv | Stage204 follows Stage203 proof-only selector equation probe. | Repair missing Stage203 records before using Stage204. |
| stage204_sources | PASS_METADATA | real_source_rows | 4 | repro/stage204_source_anchor_intake/source_access_log.csv | Accessible real public sources are recorded without committing external full snapshots. | Acquire full PDF for theorem/equation anchors. |
| stage204_claim_map | PASS_RECORDED | claim_rows | 8 | repro/stage204_source_anchor_intake/source_claim_map.csv | Source-supported metadata, platform, parameter, and warning claims are separated from unproved technical claims. | Use same-backend experiments for any speed claim. |
| stage204_boundaries | PASS_RECORDED | blocked_boundaries | 4 | repro/stage204_source_anchor_intake/claim_boundaries.csv | Full-text, benchmark, algorithm, and novelty gaps remain explicit. | Proceed to full-text anchors or same-platform benchmarks, not more speculative theory. |
| stage204_decision | PASS_STAGE204_SOURCE_ANCHOR_INTAKE_METADATA_ONLY | goal_status | active | repro/stage204_source_anchor_intake/summary.csv | Real source intake is sufficient for metadata and experiment-policy grounding only. | Continue with concrete full-text or benchmark gates. |

## Source Access Log

| source_id | kind | access_status | url | observed_support | not_supported |
| --- | --- | --- | --- | --- | --- |
| S1_eprint_landing | IACR ePrint landing | canonical_url_recorded_pdf_automated_fetch_blocked | https://eprint.iacr.org/2025/686 | Confirms the canonical public paper identifier and landing URL when accessed through browser/search metadata. | No local full-text algorithm equations or theorem anchors were extracted. |
| S2_github_readme | author implementation README | accessible | https://github.com/antoniocgj/Fast-Amortized-Bootstrapping | Build modes, AVX-512/VAES warning, r7i.metal-24xl paper-result platform, parameter families, and noise-measurement warning. | Does not replace paper theorem proofs or full source-line audit. |
| S3_askcrypto_topic | AskCryptography resource topic | accessible_metadata | https://askcryp.to/t/resource-topic-2025-686-fast-amortized-bootstrapping-with-small-keys-and-polynomial-noise-overhead/23992 | Title, paper identifier, authors, and abstract-level topic framing. | Does not provide line-level algorithm equations for this repository. |
| S4_author_page | author publication page | accessible_metadata | https://antonioguimaraes.org/publication/guimaraes-fast-2025/ | Title, abstract-level method summary, CCS 2025 appearance statement, source-reported complexity and benchmark claims. | Not a substitute for full-text proof details or our PVW/MAT-SAB contribution evidence. |

## Source Claim Map

| claim_id | support_level | sources | claim | allowed_use | not_allowed_use |
| --- | --- | --- | --- | --- | --- |
| C1_identity | metadata_supported | S2_github_readme; S3_askcrypto_topic; S4_author_page | 2025/686 is titled Fast amortized bootstrapping with small keys and polynomial noise overhead by Antonio Guimaraes and Hilder V. L. Pereira. | Paper identity and citation metadata. | No novelty or technical proof conclusion. |
| C2_publication_status | metadata_supported | S2_github_readme; S4_author_page | The implementation README and author page report the work as preprint/to appear at CCS 2025. | Source-reported venue status with date-sensitive wording. | Do not treat as independently verified proceedings metadata without a conference/proceedings source. |
| C3_source_reported_algorithm_goal | abstract_supported | S3_askcrypto_topic; S4_author_page | The source-reported method targets amortized bootstrapping with smaller keys, polynomial noise overhead, and efficient sparse polynomial multiplication. | High-level motivation and bottleneck framing. | Do not use as equation-level SAB call graph or proof of our MAT route. |
| C4_source_reported_complexity | source_reported_not_reproved | S4_author_page | The author page reports O(h) homomorphic operations per message and O(sqrt(h lambda) log lambda) noise overhead for the paper method. | Record as a source-reported baseline claim requiring full-text confirmation before theorem comparison. | Do not combine with our PVW/MAT projection as a proven theorem. |
| C5_source_reported_benchmarks | source_reported_not_reproduced | S4_author_page | The author page reports 2 to 8-bit bootstrapping in 1.46 ms to 28.5 ms and improvements over TFHE-rs in the paper's setting. | External benchmark context only. | Do not compare against our PVW/MAT-SAB numbers without same-platform reproduction. |
| C6_implementation_platform | implementation_metadata_supported | S2_github_readme | The README reports AVX-512/VAES as the primary fast build path, gives an AVX2/FMA fallback command, and says paper results use AWS r7i.metal-24xl. | Backend fairness and hardware reporting requirements. | Do not attribute our speedups to algorithmic changes without same-backend A/B. |
| C7_parameter_families | implementation_metadata_supported | S2_github_readme | The README lists binary, ternary, and arbitrary-key parameter commands including SET_2_3_2048. | Experiment matrix planning. | Does not prove correctness/noise of our modified path. |
| C8_noise_warning | implementation_metadata_supported | S2_github_readme | The README warns that measuring noise makes performance measurements unreliable and may affect correctness checks. | Separate latency runs from noise-instrumented runs. | Do not mix noise instrumentation timings into formal speed claims. |

## Claim Boundaries

| boundary_id | allowed | blocked | next_gate |
| --- | --- | --- | --- |
| B1_pdf_gap | Use metadata/abstract/README facts from accessible sources. | Full-text theorem, remark, algorithm, and equation references remain blocked until the PDF/full text is supplied or manually accessible. | Acquire reviewed full text and build a page/section anchor table. |
| B2_benchmark_gap | Use source-reported external benchmarks as context. | No paper benchmark value can be merged with our PVW/MAT-SAB result unless same metric, same backend, and same hardware are controlled. | Run same-platform baseline and PVW/MAT-SAB A/B with T_bootstrap/r as primary endpoint. |
| B3_algorithm_gap | Use sparse polynomial multiplication as the source-reported bottleneck/method axis. | No production selector/keygen change follows from metadata-only sources. | Map SAB setup, sparse_mul, CMUX/NCMUX, RGSW monomial, and extract/KS to source anchors. |
| B4_novelty_gap | Record candidate novelty questions. | No novelty claim is allowed without related-work search and full-text comparison. | Build related-work matrix after full text and post-686 works are anchored. |

## Proof Gates

| gate | status | evidence | detail | remaining_gap |
| --- | --- | --- | --- | --- |
| G1_real_sources | PASS_METADATA | repro/stage204_source_anchor_intake/source_access_log.csv | Real public source URLs and accessible metadata are recorded. | Full ePrint PDF text was not localized through automated fetch. |
| G2_claim_boundaries | PASS_RECORDED | repro/stage204_source_anchor_intake/claim_boundaries.csv | Allowed and blocked uses are separated. | No theorem/equation-level source anchors. |
| G3_experiment_policy | PASS_RECORDED | repro/stage204_source_anchor_intake/source_claim_map.csv | README hardware/backend/noise warnings are converted into benchmark policy. | Same-platform experiment rerun still required. |
| G4_production_keygen | BLOCKED | repro/stage203_production_selector_equation_probe/proof_gate.csv | Stage204 supplies source metadata only, not selector equations or keygen proof. | Production keygen/security/noise proof and full SAB A/B. |

## Next Queue

| priority | route | entry_condition | gate | current_status | evidence |
| --- | --- | --- | --- | --- | --- |
| P0 | full_text_anchor_table | A reviewed local PDF/full text of 2025/686 is available. | Map algorithm, theorem, remark, and experiment claims to page/section anchors. | waiting_full_text | repro/stage204_source_anchor_intake/proof_gate.csv |
| P1 | same_platform_benchmark_refresh | Linux/WSL or native performance platform with spqlios_avx512/AVX path is available. | Separate scalar SAB, repeated scalar, PVW/MAT-SAB, and noise-instrumented runs under T_bootstrap/r. | ready_when_compute_available | repro/stage204_source_anchor_intake/source_claim_map.csv |
| P2 | production_keygen_design | Full-text equations and code schedule are aligned. | Show selector distribution, semantic zero, noise recurrence, key size, and complete-SAB throughput. | blocked_on_full_text_and_design | repro/stage203_production_selector_equation_probe/proof_gate.csv |
