# Stage286 MAT EP Split/Counter Gate

Decision: `PASS_STAGE286_MAT_EP_SPLIT_PROXY_READY_NATIVE_COUNTER_REQUIRED`.

Stage286 turns the Stage284 MAT EP residual into concrete admission gates. It
anchors the current source, rebuilds the current MAT object for a proxy
assembly audit, and computes the component-reduction targets required to move
complete-SAB `T_bootstrap/r`. It does not claim native counter evidence or
theoretical optimality.

## Static MAT EP Split Model

| subcomponent | scope | operation_model | count_model | projected_full_share_proxy |
| --- | --- | --- | --- | --- |
| sub_decompose_diff | per MAT EP call | 5 torus-polynomial diff/decompose streams; N=2048 | 10240 | 0.604066 |
| dec_torus_to_dft | per MAT EP call | 5 torus-to-DFT conversions before dense multiply | 5 | 0.604066 |
| dense_complex_products | per AVX512 complex coefficient block | 5 rows * 5 outputs = 25 complex products | 25 | 0.604066 |
| selector_vector_loads | per AVX512 complex coefficient block | 2 * rows * outputs = 50 vector loads | 50 | 0.604066 |
| output_vector_stores | per AVX512 complex coefficient block | 2 * outputs = 10 vector stores | 10 | 0.604066 |
| cmux_from_dft_materialization | outside MAT EP timer, per CMUX | inverse DFT plus add-to output lifecycle | 573440 | 0.358366 |

## Improvement Targets

| component | profile_share | target_full_sab_speedup_vs_candidate | required_component_reduction | status |
| --- | --- | --- | --- | --- |
| mat_ep | 0.604066 | 1.03 | 0.048217 | projection_feasible_if_mechanism_exists |
| mat_ep | 0.604066 | 1.05 | 0.078831 | projection_feasible_if_mechanism_exists |
| mat_ep | 0.604066 | 1.10 | 0.150495 | projection_feasible_if_mechanism_exists |
| mat_ep | 0.604066 | 1.20 | 0.275908 | projection_feasible_if_mechanism_exists |
| cmux_from_dft | 0.358366 | 1.03 | 0.081275 | projection_feasible_if_mechanism_exists |
| cmux_from_dft | 0.358366 | 1.05 | 0.132878 | projection_feasible_if_mechanism_exists |
| cmux_from_dft | 0.358366 | 1.10 | 0.253677 | projection_feasible_if_mechanism_exists |
| cmux_from_dft | 0.358366 | 1.20 | 0.465074 | projection_feasible_if_mechanism_exists |

## Code Admission

| route | status | allowed_action | blocked_action | promotion_gate |
| --- | --- | --- | --- | --- |
| S286-A-counter_only | admitted_now | Run native counters or local assembly proxy and update ledger. | Claim theoretical MAT AVX optimality. | native/perf rows plus interpretation |
| S286-B-sub_decompose_instrumentation | admitted_instrumentation_only | Add optional counters/timers around sub_decompose, torus_to_DFT, and dense addmul. | Enable new hot-path behavior by default. | instrumented split plus unprofiled T_bootstrap/r A/B |
| S286-C-new_avx_kernel | blocked_until_split_identifies_target | Prepare isolated equivalence and microbench design. | Rewrite dense kernel based only on Stage284 Amdahl projection. | isolated correctness, microbench, full SAB repeated A/B, noise/resource |
| S286-D-body_linear_selector_format | not_admitted_by_stage286 | Keep as separate proof route. | Treat dense-kernel split as body-linear optimality proof. | distribution/security/noise proof before hot-path code |

## Claim Boundary

| claim | status | allowed_wording | forbidden_wording |
| --- | --- | --- | --- |
| mat_ep_is_current_first_target | allowed | MAT EP is the largest measured residual component in the selected candidate profile. | MAT EP is the only bottleneck or zeroing it is achievable. |
| avx512_instruction_presence | proxy_only | Current-head object/source exposes AVX512/FMA proxy evidence when objdump succeeds. | Retired load/store/FMA counters prove optimality. |
| required_component_reduction | projection_only | Improvement targets are Amdahl projections for experiment design. | The projected full-SAB improvement has been measured. |
| hot_path_edit_permission | denied_for_behavior_change | Instrumentation-only code is admissible; behavior-changing AVX work needs split evidence. | Stage286 authorizes a default hot-path rewrite. |

## Proof Gate

| gate | status | metric | value | interpretation |
| --- | --- | --- | --- | --- |
| G1_inputs | PASS | required inputs | all present | Stage286 consumes the current Stage284 frontier and current source. |
| G2_source_anchors | PASS | source anchors | all present | Split gate points at the actual MAT EP and CMUX call sites. |
| G3_tooling | PASS_PROXY | build/objdump/nm | build=PASS; objdump=PASS; nm=PASS | Current-head assembly proxy can be generated if tools pass. |
| G4_assembly_proxy | PASS_PROXY | zmm/fma proxy | zmm=239; fma_like=120 | Static proxy checks instruction presence only, not retired counters. |
| G5_native_counter_boundary | BLOCKED_OR_MISSING | perf | MISSING_OR_PERMISSION_DENIED | No hardware-counter or optimality claim without native/perf rows. |
| G6_code_admission | PASS_INSTRUMENTATION_ONLY | hot path permission | no behavior-changing hot-path edit admitted | Proceed to split instrumentation/native counters before AVX kernel rewrites. |
| G7_decision | PASS_STAGE286_MAT_EP_SPLIT_PROXY_READY_NATIVE_COUNTER_REQUIRED | stage decision | PASS_STAGE286_MAT_EP_SPLIT_PROXY_READY_NATIVE_COUNTER_REQUIRED | Proceed to native counter rerun or optional split instrumentation, not optimality claims. |

## Next Queue

| priority | route | entry_condition | gate | failure_action |
| --- | --- | --- | --- | --- |
| P0 | stage287_native_counter_rerun_or_intake | safe native authentication available | Run selected candidate with perf events for cycles, instructions, loads, stores, and 512b FP. | Keep Stage286 as proxy-only. |
| P1 | stage288_mat_ep_split_instrumentation | native counters remain unavailable | Add optional timers/counters inside MAT EP subcomponents; no default behavior change. | Do not implement new AVX kernel. |
| P2 | stage289_isolated_mat_ep_microbench | split instrumentation identifies a dominant subcomponent | Compare current kernel against one candidate under isolated equivalence and microbench. | Record neutral/negative and keep selected exact path. |
| P3 | stage290_full_sab_ab_after_kernel_candidate | isolated kernel candidate passes | Repeated complete SAB T_bootstrap/r A/B plus noise/resource. | Do not promote kernel-only speedup. |

Generated from head `2708563`.
