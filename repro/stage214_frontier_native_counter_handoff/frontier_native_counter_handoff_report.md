# Stage214 Frontier Native Counter Handoff

Decision: `PASS_STAGE214_FRONTIER_NATIVE_COUNTER_HANDOFF_READY`.

Stage214 closes the post-Stage213 local frontier without redefining the final
goal. The current exact PVW/MAT-SAB path remains the implemented baseline; the
Stage212/213 DFT wrapper is retained as a default-off negative ablation; compact
SAB remains proof-only; exact addmul/bodymajor/streaming reopen routes require
new counter-backed mechanisms.

This stage does not mark the research goal complete. It creates the native
counter handoff needed to continue without storing credentials in the repo.

## Route Ledger

| route | status | primary_evidence | decision_basis | code_permission | next_gate |
| --- | --- | --- | --- | --- | --- |
| current_exact_pvw_mat_sab | KEEP_BASELINE_AND_CLAIM_SCOPE | repro/stage206_current_head_highstat/ab_summary.csv; repro/stage207_current_head_resource_refresh/resource_comparison.csv | Current exact r-body PVW/MAT-SAB path remains the implemented complete-SAB path under T_bootstrap/r. | baseline_only | Use as regression reference for any future candidate. |
| multirow_dft_wrapper | NEGATIVE_ABLATION_NOT_PROMOTED | repro/stage213_dft_wrapper_integration_preflight/comparison.csv | Integrated MAT-EP split gate: min DFT-row speedup 0.943831823, min combined_current speedup 0.919499231. | default_off_only | Do not run complete-SAB A/B for this wrapper unless a new integrated gate reverses Stage213. |
| same_format_dft_batching_or_direct_scale | DENIED_PRIOR_GATES | repro/stage211_fft_dataflow_preflight/proof_gate.csv | Stage211 keeps old DFT batching/direct-scale routes closed unless a genuinely new primitive appears. | denied | Native counters or new backend primitive only. |
| exact_addmul_retile_bodymajor_streaming | DENIED_PRIOR_GATES | repro/stage193_exact_addmul_dataflow_preflight/summary.csv; repro/stage183_addmul_dataflow_screen/mechanism_screen.csv | Stage193 found no addmul code candidate; Stage183 records bodymajor/fulltile/streaming as prior rejected or blocked. | denied_without_new_counter_mechanism | Native counter/assembly evidence must identify a new mechanism. |
| compact_shared_output_sab | PROOF_ONLY_IMPLEMENTATION_DENIED | repro/stage192_compact_admission_route_selection/summary.csv | Compact route has unresolved key distribution, closed-state, and noise gates. | no_sab_hotpath_code | Formal structured-key/noise proof before any implementation admission. |
| tail_extract_packing_ks | DEFER_SMALL_SHARE | repro/stage208_current_head_profile_refresh/component_attribution.csv | Stage208 tail share stayed below the implementation threshold after current-head refresh. | defer | Reopen only if a new profile shows tail share is material. |
| native_hardware_counters | NEXT_EVIDENCE_ROUTE | repro/stage214_frontier_native_counter_handoff/access_probe.csv | Local WSL lacks perf; CB5 SSH port is reachable but non-interactive authentication is not configured in this session. | measurement_only | Run the Stage214 handoff script on native Linux or remote host with safe credentials. |

## Access Probe

| target | probe | status | detail |
| --- | --- | --- | --- |
| delld@192.168.107.220:22 | tcp_connect | reachable | Port reachability only; no credentials are used or stored. |
| delld@192.168.107.220 | ssh_batchmode | noninteractive_auth_not_configured | returncode=255; noninteractive authentication was not accepted |
| local_wsl | perf_path | missing |  |

## Counter Plan

| step | command | expected_output | gate |
| --- | --- | --- | --- |
| build_baseline_and_candidate | bash repro/stage214_frontier_native_counter_handoff/run_native_stage214_counters.sh | native_perf_raw/*.log | Build baseline and MAT_TRGSW_MULTIROW_DFT_WRAPPER variants on native Linux. |
| perf_split_variants | perf stat -x, -e cycles,instructions,cache-references,cache-misses,branches,branch-misses,mem_inst_retired.all_loads,mem_inst_retired.all_stores,fp_arith_inst_retired.512b_packed_double,fp_arith_inst_retired.256b_packed_double | counter logs for r=2/r=4 torus_to_dft_rows and combined_current | Counters must be collected for both baseline and wrapper builds. |
| admission_rule | compare wrapper against baseline | promotion only if combined_current improves and counters identify a new mechanism | No complete-SAB A/B is authorized from counters alone. |

## Gates

| gate | status | metric | value | evidence | detail |
| --- | --- | --- | --- | --- | --- |
| G1_stage213_frontier_input | PASS | stage213_decision | PASS_STAGE213_DFT_WRAPPER_COMPONENT_ONLY | repro/stage213_dft_wrapper_integration_preflight/proof_gate.csv | Stage214 starts after Stage213 denies complete-SAB A/B for the DFT wrapper. |
| G2_route_ledger | PASS_RECORDED | route_count | 7 | repro/stage214_frontier_native_counter_handoff/route_ledger.csv | Local hot-path routes are classified to prevent reopening rejected mechanisms without new evidence. |
| G3_local_counter_status | BLOCKED_LOCAL_WSL_NO_PERF | local_perf_path |  | repro/stage214_frontier_native_counter_handoff/access_probe.csv | Local WSL cannot provide hardware-counter attribution when perf is missing. |
| G4_remote_access_status | REMOTE_PORT_REACHABLE_AUTH_NOT_CONFIGURED | tcp;ssh_batchmode | reachable;noninteractive_auth_not_configured | repro/stage214_frontier_native_counter_handoff/access_probe.csv | Remote execution is possible only after safe non-interactive authentication or manual credential entry. |
| G5_stage214_decision | PASS_STAGE214_FRONTIER_NATIVE_COUNTER_HANDOFF_READY | decision | PASS_STAGE214_FRONTIER_NATIVE_COUNTER_HANDOFF_READY | repro/stage214_frontier_native_counter_handoff/proof_gate.csv | The next executable route is native hardware-counter collection or a new formal compact proof, not speculative local hot-path code. |

## Next Queue

| priority | route | entry_condition | gate | status | evidence |
| --- | --- | --- | --- | --- | --- |
| P0 | stage215_native_counter_execution | Native Linux perf is available and credentials are handled outside committed artifacts. | Counter logs for r=2/r=4 split variants; parse load/store/FMA/cycle/cache counters. | ready_handoff | repro/stage214_frontier_native_counter_handoff/run_native_stage214_counters.sh |
| P1 | structured_compact_formal_proof | A real proof addresses key distribution, closed state, and noise recurrence. | T1/T2/T4 proof gates before any implementation. | proof_only | repro/stage192_compact_admission_route_selection/summary.csv |
| P2 | new_hotpath_code | Stage215 counters or proof gates identify a new mechanism. | Flag-only implementation, staged equivalence, complete-SAB T_bootstrap/r A/B, noise/resource. | denied_now | repro/stage214_frontier_native_counter_handoff/route_ledger.csv |
