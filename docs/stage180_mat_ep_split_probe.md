# Stage180 MAT EP Split Probe

Decision: `PASS_STAGE180_SPLIT_PROBE_RECORDED`.

Stage180 measures the internal pieces of `mat_trgsw_mul_pvmtmlwe_sub_DFT`:

- `sub_decompose`
- `torus_to_dft_rows`
- `addmul_from_dec_dft`
- `combined_current`

The probe includes the current `mattrgsw.c` so it can call the current static
`mat_trgsw_sub_decompose` and `mat_trgsw_mul_pvmtmlwe_DFT_from_dec` boundaries.
This is a measurement gate, not an implementation change.

## Gate Summary

| gate | status | metric | value | evidence | detail | next_action |
| --- | --- | --- | --- | --- | --- | --- |
| stage180_inputs | PASS | stage179_summary_present | 1 | repro/stage179_mat_ep_microarch_audit/summary.csv | Stage180 follows the Stage179 no-code split-probe route. | Repair Stage179 first if missing. |
| stage180_remote_secret | PASS | STAGE180_SSHPASS | present | environment variable only; not written to artifacts | Remote password is consumed from environment and scrubbed from logs. | Set STAGE180_SSHPASS for CB5 execution. |
| stage180_remote_pipeline | PASS | rcs | build=0;cleanup=0;compile=0;env=0;restore_check=0;run_addmul_from_dec_dft=0;run_combined_current=0;run_sub_decompose=0;run_torus_to_dft_rows=0;sync=0;upload=0 | repro/stage180_mat_ep_split_probe | Builds MOSFHET and runs split variants under native perf on CB5. | Fix first nonzero rc before interpreting timings. |
| stage180_correctness | PASS | checks | sub_decompose:PASS;torus_to_dft_rows:PASS;addmul_from_dec_dft:PASS;combined_current:PASS | repro/stage180_mat_ep_split_probe/correctness.csv | Combined current path is checked against split decomposition/DFT/addmul for each variant run. | Do not use timings if correctness fails. |
| stage180_decision | PASS_STAGE180_SPLIT_PROBE_RECORDED | route | stage181 | repro/stage180_mat_ep_split_probe/summary.csv | Stage180 either records split data or explicitly blocks code permission. | Proceed only according to next_stage_queue. |

## Run Metrics

| variant | run_rc | r | N | items | reps | calls | total_ns | per_call_us | status | evidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| sub_decompose | 0 | 6 | 2048 | 128 | 8 | 1024 | 11006490 | 10.748525391 | PASS | repro/stage180_mat_ep_split_probe/run_sub_decompose_perf.log |
| torus_to_dft_rows | 0 | 6 | 2048 | 128 | 8 | 1024 | 17902940 | 17.483339844 | PASS | repro/stage180_mat_ep_split_probe/run_torus_to_dft_rows_perf.log |
| addmul_from_dec_dft | 0 | 6 | 2048 | 128 | 8 | 1024 | 23473624 | 22.923460937 | PASS | repro/stage180_mat_ep_split_probe/run_addmul_from_dec_dft_perf.log |
| combined_current | 0 | 6 | 2048 | 128 | 8 | 1024 | 63934247 | 62.435788086 | PASS | repro/stage180_mat_ep_split_probe/run_combined_current_perf.log |

## Derived Projection

| metric | value | unit | evidence | interpretation |
| --- | --- | --- | --- | --- |
| sub_decompose_share_of_combined | 0.172153275 | share | repro/stage180_mat_ep_split_probe/run_metrics.csv | sub_decompose share relative to current combined MAT EP/subdecomp probe. |
| torus_to_dft_rows_share_of_combined | 0.280021129 | share | repro/stage180_mat_ep_split_probe/run_metrics.csv | torus_to_dft_rows share relative to current combined MAT EP/subdecomp probe. |
| addmul_from_dec_dft_share_of_combined | 0.367152584 | share | repro/stage180_mat_ep_split_probe/run_metrics.csv | addmul_from_dec_dft share relative to current combined MAT EP/subdecomp probe. |
| split_sum_over_combined | 0.819326988 | ratio | repro/stage180_mat_ep_split_probe/run_metrics.csv | Split probes are isolated microbenches; ratio checks whether they roughly cover the combined path. |
| sub_decompose_full_sab_share_and_3pct_requirement | 0.103963271;1.389195069 | share;speedup | repro/stage180_mat_ep_split_probe/run_metrics.csv | Estimated full-SAB share and subcomponent speedup needed for a 3% complete-SAB gain. |
| torus_to_dft_rows_full_sab_share_and_3pct_requirement | 0.169104610;1.208076492 | share;speedup | repro/stage180_mat_ep_split_probe/run_metrics.csv | Estimated full-SAB share and subcomponent speedup needed for a 3% complete-SAB gain. |
| addmul_from_dec_dft_full_sab_share_and_3pct_requirement | 0.221723249;1.151228774 | share;speedup | repro/stage180_mat_ep_split_probe/run_metrics.csv | Estimated full-SAB share and subcomponent speedup needed for a 3% complete-SAB gain. |

## Next Queue

| priority | stage | name | entry_condition | gate | failure_rule |
| --- | --- | --- | --- | --- | --- |
| P0 | 181 | decide conditional implementation | Stage180 split rows are complete and correctness passes. | Open an implementation only if one subcomponent can plausibly yield >=3% full-SAB gain. | If projection is too small, close exact-path tuning. |
| P1 | 182 | negative frontier or implementation | Stage181 decision. | Either write a flag-only implementation or write the negative frontier. | No speculative retuning. |
