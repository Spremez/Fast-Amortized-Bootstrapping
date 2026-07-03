# Stage181 AVX512 Sub-Decompose Gate

Decision: `REJECT_STAGE181_SUB_DECOMP_AVX512_NOT_FASTER`.

Stage181 benchmarks the default-off `MAT_TRGSW_AVX512_SUB_DECOMP` candidate
against the baseline split probe on CB5. The candidate is allowed to proceed to
a full-SAB gate only if the combined-current projection reaches the complete
SAB `T_bootstrap/r` threshold.

## Gate Summary

| gate | status | metric | value | evidence | detail | next_action |
| --- | --- | --- | --- | --- | --- | --- |
| stage181_inputs | PASS | probe_and_source_present | 1 | repro/stage180_mat_ep_split_probe/stage180_mat_ep_split_probe.c; src/mosfhet/src/mattrgsw.c | Stage181 compares baseline and default-off AVX512 sub-decompose candidate. | Repair missing source before running. |
| stage181_remote_pipeline | PASS | rcs | build=0;cleanup=0;compile_avx512_sub_decomp=0;compile_baseline=0;run_avx512_sub_decomp_combined_current=0;run_avx512_sub_decomp_sub_decompose=0;run_baseline_combined_current=0;run_baseline_sub_decompose=0;sync=0;upload=0 | repro/stage181_sub_decomp_avx512_gate | Remote CB5 builds baseline and AVX512-subdecomp probes from the same uploaded source. | Fix first nonzero rc before interpreting results. |
| stage181_equivalence | PASS | sink_equal | sub_decompose=yes;combined_current=yes | repro/stage181_sub_decomp_avx512_gate/comparison.csv | Baseline and AVX512-subdecomp deterministic sinks must match. | Do not interpret timing if sinks differ. |
| stage181_decision | REJECT_STAGE181_SUB_DECOMP_AVX512_NOT_FASTER | route | stage182 | repro/stage181_sub_decomp_avx512_gate/comparison.csv | Promotion requires projected complete-SAB gain, not just a local kernel improvement. | Proceed according to next_stage_queue. |

## Comparison

| variant | baseline_us | avx512_us | speedup | sink_equal | projected_full_sab_speedup | status |
| --- | --- | --- | --- | --- | --- | --- |
| sub_decompose | 9.945133789 | 12.388201172 | 0.802790789 | yes | 0.975096950 | NEUTRAL_OR_FAIL |
| combined_current | 67.346628906 | 69.230082031 | 0.972794296 | yes | 0.983391514 | NEUTRAL_OR_FAIL |

## Next Queue

| priority | stage | name | entry_condition | gate | failure_rule |
| --- | --- | --- | --- | --- | --- |
| P0 | 182 | negative frontier or new mechanism | Stage181 does not promote AVX512 sub-decompose to full-SAB gate. | Record exact-path headroom and avoid blind AVX512 retuning. | No full-SAB run without a promoted microbench candidate. |
