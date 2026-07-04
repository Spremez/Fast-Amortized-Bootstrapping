# Stage301 Current-Head Direct-DFT Native Counter Refresh

Decision: `PASS_STAGE301_CURRENT_HEAD_DIRECT_DFT_NATIVE_COUNTER_REFRESH`.

Stage301 records native Linux hardware counters for the current direct-DFT
PVW/MAT-SAB candidate against the selected-control PVW path. This is
mechanism attribution only; complete-SAB speed claims remain tied to
repeated `T_bootstrap/r` campaigns.

## Run Metrics

| variant | correctness | r | pvw_avg_us | speedup_vs_scalar_repeated | t_bootstrap_over_r_pvw_us |
| --- | --- | --- | --- | --- | --- |
| direct_dft | Pass | 4 | 27683410.000 | 1.830 | 6920852.500 |
| selected_control | Pass | 4 | 31418850.000 | 1.612 | 7854712.500 |

## Counter Summary

| variant | cycles | instructions | loads | stores | fp512 | ipc | load_store_per_cycle | load_store_to_fp512 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| direct_dft | 577942108123 | 1118421167650 | 255713356630 | 144318786919 | 254957531078 | 1.935179 | 0.692166 | 1.569015 |
| selected_control | 604236527680 | 1146326517166 | 265653827215 | 147180859447 | 255019548495 | 1.897149 | 0.683234 | 1.618835 |

## Direct vs Selected

| metric | selected_control | direct_dft | selected_over_direct |
| --- | --- | --- | --- |
| cycles | 604236527680 | 577942108123 | 1.045496632 |
| instructions | 1146326517166 | 1118421167650 | 1.024950663 |
| loads | 265653827215 | 255713356630 | 1.038873490 |
| stores | 147180859447 | 144318786919 | 1.019831601 |
| fp512 | 255019548495 | 254957531078 | 1.000243246 |
| fp256 | 50408061939 | 50378295926 | 1.000590850 |
| load_store_per_cycle | 0.683234 | 0.692166 | 0.987095581 |
| load_store_to_fp512 | 1.618835 | 1.569015 | 1.031752405 |
| t_bootstrap_over_r_us | 7854712.500 | 6920852.500 | 1.134934244 |

## Proof Gate

| gate | status | metric | value | interpretation |
| --- | --- | --- | --- | --- |
| G1_runtime_secret_policy | PASS_NO_SECRET_STORED | runtime_secret | provided | Secret is consumed only from runtime environment and scrubbed from logs. |
| G2_remote_execution | PASS | remote_rcs | {'remote_unpack': 0, 'remote_install_runner': 0, 'remote_run': 0, 'remote_pull': 0} | Remote archive, runner execution, and pull must pass before interpreting counters. |
| G3_full_sab_correctness | PASS | variant_rows | 2 | Both selected-control and direct-DFT complete SAB runs must pass correctness. |
| G4_counter_capture | PASS | counter_rows | 20 | Required native counters include cycles, loads, stores and AVX512 FP arithmetic. |
| G5_claim_boundary | PASS_COUNTER_ATTRIBUTION_ONLY | scope | current_head_direct_dft | Counters support mechanism attribution only; timing claims need repeated complete-SAB runs. |
| G6_decision | PASS_STAGE301_CURRENT_HEAD_DIRECT_DFT_NATIVE_COUNTER_REFRESH | stage decision | PASS_STAGE301_CURRENT_HEAD_DIRECT_DFT_NATIVE_COUNTER_REFRESH | Controls Stage302 route. |
