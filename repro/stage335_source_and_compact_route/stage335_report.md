# Stage335 Source And Compact Route Report

Decision: `PASS_STAGE335_SHARING_MASK_FULLTEXT_AUDITED_COMPACT_SELECTOR_DENIED`.

Stage335 makes two forward moves:

1. It replaces the Stage334 metadata-only blocker for Sharing the Mask with a
   local full-text audit from the TCHES page and PDF.
2. It re-enters the implementation route by consuming Stage217/220/221/222 and
   selecting exact PVW/MAT-SAB frontier work as the next executable path.

## Summary

| decision | sharing_mask_fulltext | compact_route | selected_next |
| --- | --- | --- | --- |
| PASS_STAGE335_SHARING_MASK_FULLTEXT_AUDITED_COMPACT_SELECTOR_DENIED | audited | complete_selector_denied | stage336_exact_pvw_mat_frontier |

## Source Acquisition

| source | status | url | bytes | interpretation |
| --- | --- | --- | --- | --- |
| sharing_the_mask_2025_2112 | LOCAL_FULLTEXT_AUDITED | https://tches.iacr.org/index.php/TCHES/article/view/12434 | pdf=874805;text=134335;html=27667 | Direct high-risk prior art for common-mask/shared-mask multi-body TFHE bootstrapping. |
| paiva_et_al_2025_696 | BLOCKED_CLOUDFLARE_CHALLENGE | https://eprint.iacr.org/2025/696 | 5420 | Latest amortized-bootstrapping comparison remains metadata-only until accessible full text is registered. |
| packed_tfhe_2017_430 | BLOCKED_CLOUDFLARE_CHALLENGE | https://eprint.iacr.org/2017/430 | 5420 | Packed-TFHE prior art remains metadata-only in this automated audit. |
| mosfhet_2022_515 | FETCH_FAILED_NOT_PDF | https://eprint.iacr.org/2022/515 ; https://github.com/antoniocgj/MOSFHET | 763 | Backend/AVX optimality remains blocked; current evidence is implementation-local measurement only. |

## Sharing-The-Mask Anchors

| anchor | status | line_refs | claim_use |
| --- | --- | --- | --- |
| cm_ciphertext_definition | FOUND | 16;17;18;19;20 | Blocks broad shared-mask/common-mask novelty; not evidence for this repo's 2025/686 SAB speedup. |
| distinct_messages | FOUND | 17;18;19;20;21;22 | Blocks broad shared-mask/common-mask novelty; not evidence for this repo's 2025/686 SAB speedup. |
| tfhe_ops_extend_to_cm | FOUND | 19;20;21;22;23 | Blocks broad shared-mask/common-mask novelty; not evidence for this repo's 2025/686 SAB speedup. |
| distinct_luts | FOUND | 25;26;27;28;29 | Blocks broad shared-mask/common-mask novelty; not evidence for this repo's 2025/686 SAB speedup. |
| multi_ciphertext_bootstrapping_prior | FOUND | 102;103;104;105;106 | Blocks broad shared-mask/common-mask novelty; not evidence for this repo's 2025/686 SAB speedup. |
| bootstrapping_cost_table | FOUND | 311;312;313;314;315 | Blocks broad shared-mask/common-mask novelty; not evidence for this repo's 2025/686 SAB speedup. |
| cm_pbs_inputs | FOUND | 358;359;360;361;362 | Blocks broad shared-mask/common-mask novelty; not evidence for this repo's 2025/686 SAB speedup. |
| reported_51_percent | FOUND | 21;22;23;24;25;26;391;392;393;394 | Blocks broad shared-mask/common-mask novelty; not evidence for this repo's 2025/686 SAB speedup. |

## Claim Boundary

| claim | status | safe_wording | blocked_wording |
| --- | --- | --- | --- |
| complete_pvw_mat_sab_t_bootstrap_per_r | ALLOW_SCOPED_MEASURED | For BINARY SET_2_3_2048 on the recorded backend, current-head complete PVW/MAT-SAB improves T_bootstrap/r versus repeated scalar SAB. | Universal, all-parameter, or theorem-level speedup. |
| shared_mask_r_body_novelty | BLOCK | This work studies a 2025/686 SAB-specific PVW/MAT implementation path. | First shared-mask/common-mask multi-body TFHE bootstrapping construction. |
| compact_selector_sab_acceleration | BLOCK_CURRENT_COMPACT_STATE | Lane-local compact EP is correct in isolation, but complete selector integration is denied. | Compact selector accelerates complete SAB. |
| mat_avx_optimality | BLOCK | MAT AVX paths have measured backend evidence under recorded flags. | The current AVX implementation reaches a theoretical optimum. |

## Compact Route Audit

| stage | status | result | admission |
| --- | --- | --- | --- |
| 217 | PATTERN_ONLY | Only count-matched random dummy padding survives public-pattern probes. | no_sab_hotpath |
| 220 | KEYGEN_PROTOTYPE | Encrypted compact keygen prototype passes phase/DFT/noise negative controls. | noise_recurrence_only |
| 221 | NOISE_MODEL | Relative recurrence and T_bootstrap/r normalization permit isolated compact EP only. | isolated_ep_only |
| 222 | COMPLETE_SELECTOR_DENIED | Lane-local compact EP works, but neighbor/cross-body selector equations are missing. | return_to_exact_pvw_mat_or_new_closed_state |

## Proof Gate

| gate | status | metric | value |
| --- | --- | --- | --- |
| G1_stage334_input | PASS | Stage334 fulltext audit | present |
| G2_sharing_mask_fulltext | PASS | common-mask anchors | anchors_found |
| G3_other_fulltexts | BLOCK_METADATA_ONLY | 2025/696;2017/430;MOSFHET | not_fulltext_audited |
| G4_compact_route | DENY_COMPLETE_COMPACT_SAB | Stage222 complete selector | denied |
| G5_execution_route | PASS_STAGE335_SHARING_MASK_FULLTEXT_AUDITED_COMPACT_SELECTOR_DENIED | next executable work | stage336_exact_pvw_mat_frontier |

## Next Queue

| priority | route | gate | failure_action |
| --- | --- | --- | --- |
| P0 | stage336_exact_pvw_mat_frontier | Run same-backend exact PVW/MAT-SAB frontier refresh: current T_bootstrap/r, MAT EP attribution, and one implementable closed-path optimization candidate. | Record neutral/negative and keep exact PVW/MAT-SAB scoped result only. |
| P1 | stage336_new_neighbor_capable_compact_state_design | Finite phase oracle plus encrypted keygen/noise recurrence before any SAB code. | Do not implement compact SAB hot path. |
| P2 | fulltext_remaining_sources | Replace metadata blockers with page/line anchors. | Keep latest-work/backend optimality wording blocked. |

Generated from input head `5474393`.
