# Stage155 Same-Format Frontier Refresh

Decision: `PASS_STAGE155_SAME_FORMAT_FRONTIER_ROUTE_TO_REPRESENTATION_GATE`

Stage155 is a profile-backed route decision after Stage153/154. It does not
change scalar SAB, default PVW flags, or any hot-path code. The metric remains
the MAT-RLWE endpoint `T_complete_bootstrap(r)/r`.

Profile source: `repro/stage153_dual_sub_fullsab_gate/dual_sub_h14_r6_profile/run.log`.

Average instrumented full body time is `41394606.500 us`, or
`6899101.083 us/lane` for r=6. This is attribution-only because
profiling changes timing.

## Schedule Guard

| metric | observed_avg | expected | status | detail |
| --- | --- | --- | --- | --- |
| cmux_calls | 573440 | 573440 | PASS | (h+1)*r_prec*in_N |
| mat_ep_calls | 573440 | 573440 | PASS | one MAT external product per CMUX/NCMUX update |
| from_dft_calls | 573440 | 573440 | PASS | same-format path materializes every update |
| ncmux_calls | 5080 | 5080 | PASS | (h+1)*(2^r_prec-1) |
| sub_a_calls | 39 | 39 | PASS | one sparse subtraction per nonzero sparse secret term |
| copyback_calls | 0 | 0 | PASS | active-buffer fusion remains effective |
| dual_sub_pair_calls | 5080 | 5080 | PASS | only NCMUX/direct pairs can share the dual-sub input |

## Component Frontier

| component | avg_us | share_of_full | ceiling_if_2x_local | interpretation |
| --- | --- | --- | --- | --- |
| mat_ep | 20019803.000 | 0.483633 | 1.318942 | Largest arithmetic block; same-format dense MAT kernels remain bounded by (r+1)^2 selector work. |
| from_dft | 13496553.000 | 0.326046 | 1.194776 | Large materialization block; backend add fusion removed cmux_add, so further gain needs fewer materializations or faster IFFT. |
| sub | 6341291.000 | 0.153191 | 1.082949 | Material but Stage153 proved local pair-sharing has too little schedule coverage. |
| ncmux_auto | 369424.500 | 0.008924 | 1.004482 | Small NCMUX automorphism tail; low standalone ceiling. |
| sub_a | 918273.000 | 0.022183 | 1.011216 | Small tail; do not prioritize before larger blocks. |
| dual_sub_pair | 88215.000 | 0.002131 | 1.001067 | Explicit pair-sharing work is tiny relative to full SAB. |
| unattributed_or_timer_overlap | 161047.000 | 0.003891 | 1.001949 | Profiler overlap and residual body work; do not target without finer instrumentation. |

## Candidate Status

| candidate | latest_decision | action | reason |
| --- | --- | --- | --- |
| H14-C1 backend FromDFT-add r=6 | PASS_STAGE148_H14_R6_REPEATED_REFRESH_PROMOTION_CANDIDATE | KEEP_EXPLICIT_CURRENT_HEAD | Repeated T_bootstrap/r, noise, and resource gates pass; scalar/default unchanged. |
| r6 fulltile layout under H14 | WEAK_STAGE151_H14_R6_FULLTILE_BACKEND_TINY_POSITIVE_REPEAT_OPTIONAL | DO_NOT_PRIORITIZE | Smoke signal is tiny and older repeated fulltile evidence was negative; only rerun if a new profile-backed reason appears. |
| H14-C3 dual-sub shared-input CMUX | NEUTRAL_STAGE153_DUAL_SUB_FULLSAB_PAIR_FRACTION_LIMITED | CLOSE_LOCAL_PAIR_ROUTE | Local kernel is positive, but pairable fraction is too small to move complete SAB. |
| r6 bodymajor layout under H14 | REJECT_STAGE154_BODYMAJOR_FULLSAB_SLOWER | REJECT | Complete-SAB T_bootstrap/r is 0.977892 versus same-backend tile4. |
| same-format blind MAT layout tuning | PROFILE_BOUNDED | REQUIRE_NEW_MECHANISM | MAT EP and FromDFT are still dominant, but prior same-format layout variants do not reliably improve full SAB. |
| representation-changing lazy/DFT or compact-state route | OPEN_NEXT | SELECT_FOR_STAGE156_FEASIBILITY | Only a representation change can reduce the 573440 materializations or dense same-format work count. |

## Gate Result

| gate | status | metric | value | next_action |
| --- | --- | --- | --- | --- |
| stage155_schedule_guard | PASS | cmux;from_dft;ncmux;sub_a;copyback | 573440;573440;5080;39;0 | Stop if any schedule count differs. |
| stage155_component_frontier | PASS | mat_ep_share;from_dft_share;sub_share;sub_a_share | 0.483633;0.326046;0.153191;0.022183 | Only implement a same-format variant if it reduces these dominant counts or has a new measured mechanism. |
| stage155_candidate_closeout | PASS | closed_candidates | dual_sub_pair_route;bodymajor_layout;blind_fulltile_reruns | Move to representation-changing feasibility or native-counter attribution. |
| stage155_decision | PASS_STAGE155_SAME_FORMAT_FRONTIER_ROUTE_TO_REPRESENTATION_GATE | frontier_route | representation_changing_feasibility | Stage156 should test DFT/lazy or compact-state feasibility; do not continue blind r=6 layout tuning. |

## Next Queue

| stage | priority | name | goal | performance_gate |
| --- | --- | --- | --- | --- |
| 156 | P0 | DFT/lazy-state feasibility gate | Decide whether a PVW accumulator can remain in DFT/lazy-decomposed state across a SAB monomial update without breaking torus-domain rotations, automorphisms, or phase equality. | Count reduction must remove materializations or dense addmul work; otherwise reject before full SAB. |
| 157 | P1 | compact/shared-source production microbench refresh | Retest compact/shared-source EP with production N=2048 and decomposition/DFT reuse targets before any SAB integration. | T_kernel/r must beat dense same-format for r=4 and r=6 after decomposition/DFT cost. |
| 158 | P1 | native perf/counter refresh | Use native Linux counters to separate load/store, FMA, cache, and spill limits for the current H14 r=6 path. | Counters must explain whether MAT-aware AVX512 is memory-bound or FMA-bound. |

Interpretation: the current same-format r-body PVW/MAT-SAB path has a real
amortized complete-SAB speedup, but the remaining local same-format branches
are now bounded by full-SAB evidence. Further progress should target a
representation-changing gate that can reduce materialization count or dense
work count, not another blind r=6 layout variation.
