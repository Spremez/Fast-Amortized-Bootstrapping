# Stage177 Verified Literature/Novelty Gate

Decision: `PASS_STAGE177_VERIFIED_LITERATURE_BOUNDARY_NO_STRONG_NOVELTY_CLAIM`.

This is a bounded literature gate for the current PVW/MAT-SAB goal. It does
not attempt a broad FHE survey. It verifies enough real adjacent work to decide
which claims are currently allowed.

Result:

- strong novelty claims are denied;
- structured compact MAT-SAB remains blocked by Stage176 proof/API gaps;
- executable work should continue on exact full-MAT `T_bootstrap/r` optimization;
- any paper draft must later run citation-level verification.

## Gate Summary

| gate | status | metric | value | evidence | detail | next_action |
| --- | --- | --- | --- | --- | --- | --- |
| stage177_inputs | PASS | stage176_summary_present | 1 | repro/stage176_structured_compact_security_api_gate/summary.csv | Stage177 starts only after Stage176 redirects compact implementation to full-MAT exact path. | Repair Stage176 before interpreting literature gate. |
| stage177_verified_sources | PASS | source_rows | 10 | repro/stage177_verified_literature_novelty_gate/literature_matrix.csv | Bounded matrix records target baseline, post-686 work, amortized/batch lineage, PVW packing, TFHE/FHEW background. | Use citation-verification before any manuscript sentence. |
| stage177_direct_prior_art | NO_DIRECT_COMPACT_MATCH_IN_BOUNDED_SEARCH | direct_compact_pvw_mat_sab_rows | 0 | repro/stage177_verified_literature_novelty_gate/novelty_risk.csv | No verified source in this bounded search directly implements our proposed structured compact PVW/MAT-SAB route. | Do not convert this into a novelty claim; bounded search is not exhaustive. |
| stage177_adjacent_prior_art | HIGH | adjacent_rows | 5 | repro/stage177_verified_literature_novelty_gate/literature_matrix.csv | 2025/696 and several amortized/batch bootstrapping works create high novelty risk for broad claims. | Any paper claim must be narrow and compared against these sources. |
| stage177_strong_novelty_permission | DENY | permission_yes | 0 | repro/stage177_verified_literature_novelty_gate/claim_policy.csv | Strong novelty claims are blocked until security/API proof, complete-SAB implementation, and related-work comparison are complete. | Proceed to exact full-MAT T_bootstrap/r engineering frontier. |
| stage177_decision | PASS_STAGE177_VERIFIED_LITERATURE_BOUNDARY_NO_STRONG_NOVELTY_CLAIM | route | stage178_full_mat_exact_path | repro/stage177_verified_literature_novelty_gate/summary.csv | Literature gate supports cautious engineering claims only and routes next to measured exact-path optimization. | Run Stage178. |

## Targeted Queries

| axis | query | purpose |
| --- | --- | --- |
| target-paper | eprint 2025/686 sparse amortized bootstrapping | Verify the baseline target and implementation repository. |
| post-686 | Faster amortized bootstrapping using the incomplete NTT for free 2025/696 | Find direct follow-up/neighbor after 2025/686. |
| amortized-history | Amortized Bootstrapping Revisited 2023/014 | Verify the 686 lineage and earlier implementation evidence. |
| ring-automorphism | Faster Amortized FHEW bootstrapping using Ring Automorphisms 2023/112 | Map adjacent NTT/automorphism amortized bootstrapping. |
| functional-batch | Amortized Functional Bootstrapping less than 7ms 2023/910 | Map batch functional bootstrapping and amortized per-ciphertext claims. |
| batch-framework | Batch Bootstrapping I II SIMD Bootstrapping polynomial modulus EUROCRYPT 2023 | Map batch/SIMD bootstrapping alternatives. |
| pvw-packing | Packed Ciphertexts in LWE-Based Homomorphic Encryption PVW 2012/565 | Verify PVW packing ancestry. |
| tfhe-external-product | TFHE Fast Fully Homomorphic Encryption over the Torus external product 2018/421 | Verify TFHE/GSW external-product baseline. |
| fhew-origin | FHEW bootstrapping homomorphic encryption in less than a second 2014/816 | Verify FHEW predecessor. |
| ring-packing | Ring Packing and Amortized FHEW Bootstrapping ICALP 2018 | Verify the original amortized FHEW line. |

## Related-Work Matrix

| id | title | authors_year | venue_or_archive | url | relation_to_project | similarity | difference | novelty_risk | local_claim_allowed |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| GP2025_686 | Fast amortized bootstrapping with small keys and polynomial noise overhead | Antonio Guimaraes; Hilder V. L. Pereira; 2025 | IACR ePrint 2025/686; repository states to appear at CCS 2025 | https://eprint.iacr.org/2025/686 | Target baseline; current repository implements and extends this SAB line. | Sparse amortized bootstrapping, small keys, polynomial noise overhead, AVX512-oriented implementation. | Our work changes implementation/representation using PVW/MAT r-body lanes and measures T_bootstrap/r against repeated scalar SAB. | HIGH_BASELINE | Use as baseline and target algorithm only. |
| PDMHSY2025_696 | Faster amortized bootstrapping using the incomplete NTT for free | Thales B. Paiva; Gabrielle De Micheli; Syed Mahbub Hafiz; Marcos A. Simplicio Jr.; Bahattin Yildiz; 2025 | IACR ePrint 2025/696 | https://eprint.iacr.org/2025/696 | Direct post-686 adjacent work. | Improves amortized bootstrapping around the Guimaraes et al. line via NTT strategy and reports speed/DFR tradeoffs. | Optimizes NTT/amortized algorithm, not PVW/MAT shared-mask r-body external product in this codebase. | HIGH_DIRECT_ADJACENT | Any paper claim must compare or position against this work. |
| GPL2023_014 | Amortized Bootstrapping Revisited: Simpler, Asymptotically-faster, Implemented | Antonio Guimaraes; Hilder V. L. Pereira; Barry van Leeuwen; 2023 | IACR ePrint 2023/014; ASIACRYPT 2023 | https://eprint.iacr.org/2023/014 | Algorithmic ancestor for practical amortized bootstrapping. | Amortized bootstrapping with concrete implementation; double-CRT GSW and shrinking. | Not the sparse 2025/686 SAB implementation and not our PVW/MAT r-body path. | MEDIUM_LINEAGE | Cite as lineage and complexity context. |
| DKMS2023_112 | Faster Amortized FHEW bootstrapping using Ring Automorphisms | Gabrielle De Micheli; Duhyeong Kim; Daniele Micciancio; Adam Suhl; 2023/PKC 2024 | IACR ePrint 2023/112; PKC 2024 | https://eprint.iacr.org/2023/112 | Adjacent amortized FHEW algorithmic work. | Uses NTT/ring automorphisms and scheme switching to reduce amortized bootstrapping overhead. | Not 686 SAB and not PVW/MAT shared-mask external product. | MEDIUM_ADJACENT | Cite for amortized bootstrapping landscape. |
| LW2023_910 | Amortized Functional Bootstrapping in less than 7ms, with O~(1) polynomial multiplications | Zeyu Liu; Yunhao Wang; 2023 | IACR ePrint 2023/910; ASIACRYPT 2023 | https://eprint.iacr.org/2023/910 | Adjacent batch functional bootstrapping. | Amortized/batched LWE bootstrapping with concrete implementation and per-ciphertext timing claims. | Different framework/objective; not sparse 686 SAB and not MAT external-product batching. | MEDIUM_ADJACENT | Cite for amortized functional bootstrapping context. |
| LW2023_BatchI_II | Batch Bootstrapping I/II | Feng-Hao Liu; Han Wang; 2023 | EUROCRYPT 2023 | https://link.springer.com/content/pdf/10.1007/978-3-031-30620-4_11.pdf | Alternative SIMD/batch bootstrapping framework. | Batch/SIMD bootstrapping in polynomial modulus; relevant to amortized throughput claims. | Different mathematical framework and not 686 sparse schedule/PVW-MAT path. | MEDIUM_ADJACENT | Cite as adjacent batch bootstrapping prior art. |
| BGH2012_565 | Packed Ciphertexts in LWE-Based Homomorphic Encryption | Zvika Brakerski; Craig Gentry; Shai Halevi; 2012 | IACR ePrint 2012/565 | https://eprint.iacr.org/2012/565 | PVW packing ancestry. | Uses Peikert-Vaikuntanathan-Waters packing for SIMD-style LWE ciphertexts. | Packing primitive/background, not SAB external-product algorithm. | LOW_BACKGROUND_HIGH_IF_PACKING_CLAIM | Cite for PVW packing background; do not claim PVW packing as new. |
| CGGI2018_421 | TFHE: Fast Fully Homomorphic Encryption over the Torus | Ilaria Chillotti; Nicolas Gama; Mariya Georgieva; Malika Izabachene; 2018/2019 | IACR ePrint 2018/421; Journal of Cryptology 2019 | https://eprint.iacr.org/2018/421 | TFHE/GSW external-product baseline. | External product between GSW and LWE/RLWE-like ciphertexts; bootstrapping and packed operations. | Not amortized 686 SAB and not current MAT/PVW multi-body implementation. | BACKGROUND_REQUIRED | Cite for TFHE/external-product background. |
| DM2014_816 | FHEW: Bootstrapping Homomorphic Encryption in less than a second | Leo Ducas; Daniele Micciancio; 2014/2015 | IACR ePrint 2014/816; EUROCRYPT 2015 | https://eprint.iacr.org/2014/816 | FHEW predecessor to TFHE/amortized FHEW lines. | Bootstrapping of bit operations and FHEW-style lineage. | Single/sequential bootstrapping baseline, not multi-lane MAT-SAB. | BACKGROUND_REQUIRED | Cite for FHEW background. |
| MS2018_ICALP | Ring Packing and Amortized FHEW Bootstrapping | Daniele Micciancio; Jessica Sorrell; 2018 | ICALP 2018 | https://drops.dagstuhl.de/entities/document/10.4230/LIPIcs.ICALP.2018.100 | Original amortized FHEW-style bootstrapping line. | Refreshes many messages simultaneously and establishes amortized FHEW bootstrapping context. | Earlier ring-packing/Nussbaumer-style line, not sparse 686 SAB or PVW/MAT external-product batching. | BACKGROUND_REQUIRED | Cite for original amortized bootstrapping context. |

## Novelty Risk

| claim | risk | reason | required_next_evidence | allowed_status |
| --- | --- | --- | --- | --- |
| PVW/MAT-SAB exact full path improves repeated scalar SAB throughput on this implementation | LOW_TO_MEDIUM | This is an implementation/experimental claim tied to local complete-SAB A/B evidence, not a broad novelty claim. | Stage178 must re-normalize T_bootstrap/r and cite commit/backend/raw logs. | ENGINEERING_CLAIM_ONLY |
| Structured compact MAT-SAB is a new implemented bootstrapping algorithm | HIGH_BLOCKED | Stage176 denies implementation permission; literature contains strong adjacent amortized/batch work. | Security/API proof plus full-SAB implementation and comparison to 2025/696. | FORBIDDEN_NOW |
| PVW packing itself is novel | INVALID | PVW packing is established prior art; BGH2012 explicitly uses it for LWE-based packed ciphertexts. | None; do not make this claim. | FORBIDDEN |
| AVX512 MAT external product is a paper-level algorithmic contribution | MEDIUM | It may be valuable systems work, but must be separated from mathematical SAB algorithm claims and compared at complete-SAB level. | ISA-specific microbench, disassembly/counters, full-SAB A/B, backend separation. | POSSIBLE_SYSTEMS_ABLATION |
| 2025/686 SAB can be accelerated by optimizing exact full-MAT r-body batching | MEDIUM | Current measurements support some T_bootstrap/r gain, but not theoretical optimality or multi-fold guarantee. | Stage178/179 exact-path component-driven gates and repeated complete-SAB benchmarks. | ACTIVE_ENGINEERING_ROUTE |

## Citation Support

| local_claim | supporting_sources | support_strength | needs_cite_verify |
| --- | --- | --- | --- |
| 686 is the baseline target and implementation source | GP2025_686 | STRONG_FOR_BASELINE | YES_BEFORE_PAPER |
| 2025/696 is direct adjacent/follow-up work after 686 | PDMHSY2025_696 | STRONG_FOR_RELATED_WORK | YES_BEFORE_PAPER |
| Amortized bootstrapping has a substantial prior lineage | MS2018_ICALP; GPL2023_014; DKMS2023_112; LW2023_910; LW2023_BatchI_II | STRONG | YES_BEFORE_PAPER |
| PVW packing is prior art and cannot be claimed as new | BGH2012_565 | STRONG | YES_BEFORE_PAPER |
| TFHE/FHEW external product is background prior art | CGGI2018_421; DM2014_816 | STRONG | YES_BEFORE_PAPER |

## Claim Policy

| scope | allowed | forbidden |
| --- | --- | --- |
| paper_abstract | We explore an implementation-level PVW/MAT r-body acceleration path for 2025/686-style SAB. | We introduce a new compact MAT-SAB algorithm. |
| performance_claim | Report complete-SAB T_bootstrap/r speedups with backend, commit, seed, and CI. | Report kernel-only speedups as bootstrapping acceleration. |
| compact_claim | Structured compact is a blocked proof route with finite/toy evidence. | Omitted zero encryptions are secure under standard RLWE without proof. |
| novelty_claim | Claim only after proof, full benchmarks, and explicit comparison to 2025/696 and batch/amortized work. | Use 'novel' based only on local code search or bounded web search. |

## Next Queue

| priority | stage | name | entry_condition | gate | failure_rule |
| --- | --- | --- | --- | --- | --- |
| P0 | 178 | full-MAT exact path per-bit throughput frontier | Stage176 denies compact implementation; Stage177 denies strong novelty claim. | Re-normalize all current complete-SAB evidence as T_bootstrap/r and choose the next exact-path implementation candidate from measured component shares. | No new implementation branch unless the candidate can affect complete-SAB T_bootstrap/r. |
| P1 | 179 | complete-SAB exact-path experiment loop | Stage178 selects a candidate with plausible complete-SAB impact. | Run correctness, microbench, full-SAB repeated A/B, attribution, noise/resource. | Neutral/reject candidates are recorded and not retuned without a new mechanism. |
| P2 | 180 | paper-citation verification | A manuscript or paper-style claims are drafted. | Every cited sentence must be checked against source text or official metadata. | Unsupported statements are removed or downgraded. |
