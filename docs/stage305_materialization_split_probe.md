# Stage305 Materialization Split Probe

Decision: `PASS_STAGE305_MATERIALIZATION_SPLIT_PROFILE_RECORDED`.

Stage305 compares selected-control and direct-DFT with body and MAT-EP split profiling enabled. Instrumented times are used for component attribution only.

## Summary

| variant | correctness | t_bootstrap_over_r_pvw_us | body_mat_ep_us_sum | split_total_us | split_vs_body_mat_ep_ratio |
| --- | --- | --- | --- | --- | --- |
| selected_control | Pass | 6687778.750 | 32237088.000 | 32140708.000 | 0.997010 |
| direct_dft | Pass | 6259014.000 | 28544941.000 | 28455839.000 | 0.996879 |

## Components

| variant | component | us | share_of_split_total | avg_us_per_call |
| --- | --- | --- | --- | --- |
| selected_control | decompose | 8651834.000 | 0.269186 | 7.543801 |
| selected_control | torus_to_dft | 12148431.000 | 0.377976 | 10.592591 |
| selected_control | dense_from_dec | 11191490.000 | 0.348203 | 9.758205 |
| direct_dft | decompose | 58244.000 | 0.002047 | 0.050785 |
| direct_dft | torus_to_dft | 17547350.000 | 0.616652 | 15.300075 |
| direct_dft | dense_from_dec | 10760686.000 | 0.378154 | 9.382574 |

## Comparison

| metric | selected_control | direct_dft | selected_over_direct |
| --- | --- | --- | --- |
| t_bootstrap_over_r_pvw_us | 6687778.750 | 6259014.000 | 1.068504 |
| body_mat_ep_us_sum | 32237088.000 | 28544941.000 | 1.129345 |
| split_total_us | 32140708.000 | 28455839.000 | 1.129494 |
| decompose | 8651834.000 | 58244.000 | 148.544640 |
| torus_to_dft | 12148431.000 | 17547350.000 | 0.692323 |
| dense_from_dec | 11191490.000 | 10760686.000 | 1.040035 |

## Proof Gate

| gate | status | metric | value | interpretation |
| --- | --- | --- | --- | --- |
| G1_correctness | PASS | variants | selected_control;direct_dft | Both profiled variants must pass target correctness. |
| G2_profile_consistency | PASS | calls/rows | matched | Split calls and rows must match body-profile MAT EP calls. |
| G3_dominant_direct_component | RECORDED | component | torus_to_dft | Dominant direct residual component selects the next micro-hypothesis. |
| G4_claim_boundary | PASS_PROFILE_ONLY | scope | instrumented one-run profile | Do not use instrumented latency as final speed claim. |
| G5_decision | PASS_STAGE305_MATERIALIZATION_SPLIT_PROFILE_RECORDED | stage decision | PASS_STAGE305_MATERIALIZATION_SPLIT_PROFILE_RECORDED | Controls Stage306 route. |
