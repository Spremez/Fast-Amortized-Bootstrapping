# Stage286 MAT EP Counter Validation Plan

## Immediate Work

| priority | route | entry_condition | gate | failure_action |
| --- | --- | --- | --- | --- |
| P0 | stage287_native_counter_rerun_or_intake | safe native authentication available | Run selected candidate with perf events for cycles, instructions, loads, stores, and 512b FP. | Keep Stage286 as proxy-only. |
| P1 | stage288_mat_ep_split_instrumentation | native counters remain unavailable | Add optional timers/counters inside MAT EP subcomponents; no default behavior change. | Do not implement new AVX kernel. |
| P2 | stage289_isolated_mat_ep_microbench | split instrumentation identifies a dominant subcomponent | Compare current kernel against one candidate under isolated equivalence and microbench. | Record neutral/negative and keep selected exact path. |
| P3 | stage290_full_sab_ab_after_kernel_candidate | isolated kernel candidate passes | Repeated complete SAB T_bootstrap/r A/B plus noise/resource. | Do not promote kernel-only speedup. |

## Required Events For Native Counter Runs

- cycles
- instructions
- cache references/misses where available
- retired loads/stores where available
- 512-bit packed double FP events where available

## Required Statistics For Promotion

- unprofiled repeated complete-SAB `T_bootstrap/r`;
- same-backend control;
- correctness and noise/resource gates;
- raw logs and artifact hashes;
- claim boundary separating proxy, counter, kernel, and full SAB evidence.
