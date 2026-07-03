# Stage188 Scoped Manuscript Skeleton

Decision: `PASS_STAGE188_SCOPED_MANUSCRIPT_SKELETON_READY`.

Stage188 creates a manuscript skeleton that is constrained by the current
claim ledger. It is not a final paper. It exists to prevent claim drift while
making the current implemented result and open proof obligations readable.

## Gate Summary

| gate | status | metric | value | evidence | detail | next_action |
| --- | --- | --- | --- | --- | --- | --- |
| stage188_inputs | PASS | required_inputs_present | 1 | repro/stage185_research_repro_package_refresh/claim_table.csv; repro/stage187_compact_proof_obligation_draft/theorem_matrix.csv | Stage188 consumes scoped claim ledger, compact proof obligations, literature matrix, and experiment evidence. | Repair missing inputs before manuscript use. |
| stage188_manuscript_skeleton | PASS_DRAFTED | sections | 7 | repro/stage188_scoped_manuscript_skeleton/manuscript_skeleton.md | Manuscript skeleton is scoped to allowed current claims. | Use as outline only; final paper still needs citation verification. |
| stage188_forbidden_claim_guard | PASS | forbidden_hits | 0 | repro/stage188_scoped_manuscript_skeleton/claim_guard.csv | Generated skeleton avoids forbidden compact/optimality claims. | Fix skeleton before commit if nonzero. |
| stage188_decision | PASS_STAGE188_SCOPED_MANUSCRIPT_SKELETON_READY | route | scoped_manuscript_ready | repro/stage188_scoped_manuscript_skeleton/summary.csv | The artifact is a manuscript skeleton, not a final paper or novelty proof. | Proceed to citation verification or targeted proof probes. |

## Section Evidence Matrix

| section | allowed_content | evidence | guardrail |
| --- | --- | --- | --- |
| Introduction | Motivate per-lane SAB throughput and define T_bootstrap/r as the endpoint. | repro/stage185_research_repro_package_refresh/requirement_matrix.csv; repro/stage178_fullmat_perbit_frontier/per_bit_throughput.csv | No broad novelty or theoretical optimum language. |
| Background and Related Work | Position against 2025/686, 2025/696, amortized/batch bootstrapping, PVW packing, TFHE/FHEW. | repro/stage177_verified_literature_novelty_gate/literature_matrix.csv | Every final citation sentence needs source-level verification before submission. |
| Algorithm Object | Describe exact PVW/MAT-SAB as r-body shared-mask MAT-RLWE bootstrapping. | repro/stage185_research_repro_package_refresh/requirement_matrix.csv | Do not call compact/shared-output SAB implemented. |
| Complexity and Boundaries | Report dense full-MAT same-format counts and measured Amdahl requirements. | repro/stage180_mat_ep_split_probe/derived_projection.csv | State partial lower-bound model, not formal optimality. |
| Implementation | Describe explicit sab_pvw path, MAT-aware AVX512 variants, and negative ablations. | repro/stage181_sub_decomp_avx512_gate/comparison.csv; repro/stage185_research_repro_package_refresh/claim_table.csv | Do not claim AVX512 sub-decompose optimization. |
| Experiments | Report complete-SAB T_bootstrap/r A/B and rejected component candidates. | repro/stage178_fullmat_perbit_frontier/per_bit_throughput.csv; repro/stage181_sub_decomp_avx512_gate/comparison.csv | Kernel-only results cannot be reported as bootstrapping speedup. |
| Limitations and Future Work | Explain compact proof obligations and exact-route no-code boundary. | repro/stage186_compact_proof_unlock_audit/summary.csv; repro/stage187_compact_proof_obligation_draft/theorem_matrix.csv | Compact remains proof-gated future work. |

## Claim Guard

| claim | status | safe_text | forbidden_text | evidence |
| --- | --- | --- | --- | --- |
| complete_sab_amortized_speedup | allowed_scoped | Under recorded platform/backend/parameters, the exact PVW/MAT-SAB path has complete-SAB T_bootstrap/r speedup over repeated scalar SAB. | Do not generalize to theoretical optimality, all parameters, or all branches. | repro/stage178_fullmat_perbit_frontier/per_bit_throughput.csv |
| avx512_sub_decompose_optimization | denied | The default-off AVX512 sub-decompose path is a negative ablation. | Do not call this path a speedup or run a full-SAB claim from it. | repro/stage181_sub_decomp_avx512_gate/comparison.csv |
| mat_avx512_theoretical_optimality | denied | MAT-aware AVX512 implementations exist and are bounded by measured gates. | Do not claim optimal AVX512 or optimal MAT external product. | repro/stage182_exact_path_negative_frontier/claim_permissions.csv; repro/stage183_addmul_dataflow_screen/mechanism_screen.csv |
| new_compact_mat_sab_algorithm_implemented | denied_blocked | Compact/shared-output MAT-SAB remains a proof/literature route. | Do not claim compact SAB implementation, speedup, or novelty. | repro/stage176_structured_compact_security_api_gate/summary.csv; repro/stage177_verified_literature_novelty_gate/summary.csv |
| compact_future_work | future_work_only | Compact/shared-output MAT-SAB is a proof-gated future route with kernel-level motivation. | Compact/shared-output MAT-SAB is implemented or has complete-SAB speedup. | repro/stage186_compact_proof_unlock_audit/summary.csv; repro/stage187_compact_proof_obligation_draft/theorem_matrix.csv |

## Citation TODO

| id | title | role | url | required_action |
| --- | --- | --- | --- | --- |
| GP2025_686 | Fast amortized bootstrapping with small keys and polynomial noise overhead | Target baseline; current repository implements and extends this SAB line. | https://eprint.iacr.org/2025/686 | cite_verify_before_submission |
| PDMHSY2025_696 | Faster amortized bootstrapping using the incomplete NTT for free | Direct post-686 adjacent work. | https://eprint.iacr.org/2025/696 | cite_verify_before_submission |
| GPL2023_014 | Amortized Bootstrapping Revisited: Simpler, Asymptotically-faster, Implemented | Algorithmic ancestor for practical amortized bootstrapping. | https://eprint.iacr.org/2023/014 | cite_verify_before_submission |
| DKMS2023_112 | Faster Amortized FHEW bootstrapping using Ring Automorphisms | Adjacent amortized FHEW algorithmic work. | https://eprint.iacr.org/2023/112 | cite_verify_before_submission |
| LW2023_910 | Amortized Functional Bootstrapping in less than 7ms, with O~(1) polynomial multiplications | Adjacent batch functional bootstrapping. | https://eprint.iacr.org/2023/910 | cite_verify_before_submission |
| LW2023_BatchI_II | Batch Bootstrapping I/II | Alternative SIMD/batch bootstrapping framework. | https://link.springer.com/content/pdf/10.1007/978-3-031-30620-4_11.pdf | cite_verify_before_submission |
| BGH2012_565 | Packed Ciphertexts in LWE-Based Homomorphic Encryption | PVW packing ancestry. | https://eprint.iacr.org/2012/565 | cite_verify_before_submission |
| CGGI2018_421 | TFHE: Fast Fully Homomorphic Encryption over the Torus | TFHE/GSW external-product baseline. | https://eprint.iacr.org/2018/421 | cite_verify_before_submission |
| DM2014_816 | FHEW: Bootstrapping Homomorphic Encryption in less than a second | FHEW predecessor to TFHE/amortized FHEW lines. | https://eprint.iacr.org/2014/816 | cite_verify_before_submission |
| MS2018_ICALP | Ring Packing and Amortized FHEW Bootstrapping | Original amortized FHEW-style bootstrapping line. | https://drops.dagstuhl.de/entities/document/10.4230/LIPIcs.ICALP.2018.100 | cite_verify_before_submission |

## Experiment Table Plan

| table | rows | primary_metric | current_values | evidence |
| --- | --- | --- | --- | --- |
| Complete SAB amortized throughput | exact PVW/MAT-SAB r=6 versus repeated scalar | T_bootstrap/r | mean 1.131666667x; min 1.115000000x; CI-low 1.095041982x | repro/stage178_fullmat_perbit_frontier/per_bit_throughput.csv |
| Component projection and Amdahl requirements | sub-decompose, torus-to-DFT rows, addmul | component share and speedup required for 3pct full-SAB gain | sub 0.103963271;1.389195069; dft 0.169104610;1.208076492; addmul 0.221723249;1.151228774 | repro/stage180_mat_ep_split_probe/derived_projection.csv |
| Negative AVX512 sub-decompose ablation | baseline versus default-off AVX512 sub-decompose | combined_current speedup | 0.972794296x | repro/stage181_sub_decomp_avx512_gate/comparison.csv |
| Compact proof status | T1-T6 proof obligations | implementation permission | production SAB code denied | repro/stage187_compact_proof_obligation_draft/implementation_entry_rule.csv |
