# Stage265 Current-Head Counter Reuse Audit

Decision: `PASS_STAGE265_CURRENT_HEAD_COUNTER_REUSE_AUDIT_REFRESH_REQUIRED`.

Stage265 reconciles the current-head Stage264 proxy audit with the older
Stage101/226 native counter evidence. It does not run a new benchmark and does
not change SAB code. Its purpose is to prevent using historical native counters
as proof for the current non-binary include-zero/ternary `T_bootstrap/r` path.

## Code Delta From Stage245 Bridge Anchor

| path | status | classification | claim_effect |
| --- | --- | --- | --- |
| include/sab_pvw.h | M | pvw_sab_hot_path | Complete-SAB counter attribution for PVW/MAT path requires fresh current-head native run |
| main.c | M | benchmark_and_protocol_harness | Benchmark semantics and current target claims require fresh current-head evidence |
| src/mosfhet/Makefile.def | M | build_flags | Backend/flag build semantics require current-binary verification |
| src/sab_pvw.c | M | pvw_sab_hot_path | Complete-SAB counter attribution for PVW/MAT path requires fresh current-head native run |

## MAT Kernel Delta

| path | status | classification | claim_effect |
| --- | --- | --- | --- |
| src/mosfhet/src/mattrgsw.c | NO_DIFF | unchanged | prior attribution may remain structurally reusable for this path set |

## Evidence Reuse Matrix

| evidence | input_status | reuse_for_current_nonbinary_claim | reason |
| --- | --- | --- | --- |
| Stage101 CB5 native r=4 binary counters | present | historical_context_only | Stage101 predates the current non-binary SAB path and does not measure include-zero/ternary target T_bootstrap/r. |
| Stage226 exact backend-vs-wrapper native counters | present | not_directly_reusable | PVW/SAB hot-path and benchmark code changed after the Stage245 bridge; Stage226 remains exact-route mechanism context only. |
| Stage245 current-head counter bridge | present | expired_by_current_hotpath_delta | Stage245 bridged only through commit 0888285; current HEAD changes include main.c, sab_pvw.c, sab_pvw.h, and Makefile.def. |
| Stage263 current non-binary profile | present | current_profile_evidence | Stage263 measures current non-binary schedule/profile but not native hardware counters. |
| Stage264 current MAT-AVX512 proxy | present | current_proxy_only | Stage264 audits the current object/source proxy; WSL perf is missing, so it is not native counter evidence. |
| MAT external-product kernel source | unchanged_since_stage245 | kernel_structure_context | The MAT EP source is unchanged, but complete-SAB native counters still require fresh measurement after wrapper/protocol deltas. |
| Stage226 attribution ratios | present | context_only | Prior exact-route ratios: cycles=1.017861569, loads=1.011560486, stores=1.009880546. |

## Claim Boundary

| claim | status | allowed_wording | forbidden_wording |
| --- | --- | --- | --- |
| current_nonbinary_t_bootstrap_over_r | supported_by_stage262_263_wsl | Use Stage262 repeated WSL and Stage263 profile evidence for current non-binary T_bootstrap/r claims. | Treat historical native counters as current non-binary native-counter evidence. |
| current_head_native_counter_attribution | fresh_native_run_required | Historical counters are context; current non-binary include-zero/ternary native counters must be rerun on the current binary. | Stage101/226 counters prove current non-binary MAT-SAB hardware behavior. |
| mat_kernel_source_stability | supported | mattrgsw.c is unchanged from the Stage245 bridge anchor, so source-level MAT EP structure is stable. | Stable source alone proves retired counter behavior or theoretical optimality. |
| theoretical_optimality | blocked | Keep MAT-AVX512 optimality open pending lower-bound/counter/model closure. | The current MAT-AVX512 implementation has reached theoretical optimum. |

## Next Stage Queue

| priority | route | entry_condition | gate | status | failure_action |
| --- | --- | --- | --- | --- | --- |
| P0 | stage266_current_head_nonbinary_native_counter | Need hardware-counter attribution for current non-binary include-zero/ternary T_bootstrap/r. | Native perf on current HEAD, same backend, full SAB correctness, counters for r=4 include-zero and ternary. | selected_if_remote_available | Keep native-counter claim historical/context-only. |
| P1 | stage266_local_nonbinary_split_projection | Native perf unavailable but local WSL can run current binary. | Profile split projection only; no hardware-counter or optimality wording. | fallback | Do not alter SAB hot path without full T_bootstrap/r A/B gate. |
| P2 | new_hotpath_variant | A concrete implementation mechanism is selected after Stage266 evidence. | correctness, noise/resource, repeated complete-SAB T_bootstrap/r, backend separation. | blocked_until_evidence | Record neutral/negative; preserve scalar baseline. |

## Proof Gate

| gate | status | metric | value | interpretation |
| --- | --- | --- | --- | --- |
| G1_inputs | PASS | required prior evidence | Stage101 CB5 native r=4 binary counters=present;Stage226 exact backend-vs-wrapper native counters=present;Stage245 current-head counter bridge=present;Stage263 current non-binary profile=present;Stage264 current MAT-AVX512 proxy=present;MAT external-product kernel source=unchanged_since_stage245;Stage226 attribution ratios=present | Prior native/proxy/profile artifacts must be present before reuse is classified. |
| G2_hotpath_delta | REFRESH_REQUIRED | Stage245 anchor to current HEAD executable diff | diff_present | Current non-binary complete-SAB native counter claims require a fresh current-head run. |
| G3_mat_kernel_delta | PASS_UNCHANGED | mattrgsw.c delta | no_diff | MAT EP source stability preserves source-structure context but not complete-SAB counter reuse. |
| G4_claim_boundary | PASS | historical counters scoped | context_only | Stage101/226 counters must not be cited as current non-binary native evidence. |
| G5_next_route | SELECT_STAGE266_CURRENT_HEAD_NATIVE_COUNTER | next executable route | stage266_current_head_nonbinary_native_counter | The next non-theory step is fresh current-head non-binary native-counter attribution if remote execution is available. |
| G6_decision | PASS_STAGE265_CURRENT_HEAD_COUNTER_REUSE_AUDIT_REFRESH_REQUIRED | stage decision | PASS_STAGE265_CURRENT_HEAD_COUNTER_REUSE_AUDIT_REFRESH_REQUIRED | Stage265 prevents overclaiming historical counters and selects a concrete next experiment. |

Generated from input head `6f04818`. Stage264 baseline head: `6f04818`.
