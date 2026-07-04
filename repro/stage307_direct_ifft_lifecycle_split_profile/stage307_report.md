# Stage307 Direct IFFT Lifecycle Split Profile

Decision: `PASS_STAGE307_DIRECT_IFFT_LIFECYCLE_PROFILE_RECORDED`.

Stage307 adds profile-only instrumentation under `MAT_TRGSW_DIRECT_DFT_PROFILE=true` and splits the direct sub-DTF materialization block into digit-to-double and reverse-FFT time.

## Summary

| decision | correctness | t_bootstrap_over_r_pvw_us | split_sub_calls | direct_profile_calls | direct_rows_sum | direct_profile_vs_split_dft_ratio | dominant_direct_subcomponent |
| --- | --- | --- | --- | --- | --- | --- | --- |
| PASS_STAGE307_DIRECT_IFFT_LIFECYCLE_PROFILE_RECORDED | Pass | 6231227.250 | 1126560 | 1126560 | 5632800 | 0.984943 | ifft |

## Lifecycle Components

| component | us | share_of_direct_profile_total | avg_us_per_direct_call | avg_us_per_row |
| --- | --- | --- | --- | --- |
| digit_to_double | 8487031.000 | 0.481687 | 7.533581 | 1.506716 |
| ifft | 8890344.000 | 0.504577 | 7.891585 | 1.578317 |
| accounting_gap | 242030.000 | 0.013737 |  |  |

## Proof Gate

| gate | status | metric | value | interpretation |
| --- | --- | --- | --- | --- |
| G1_correctness | PASS | target_full correctness | Pass | Profile-only instrumentation must preserve complete SAB correctness. |
| G2_row_consistency | PASS | direct rows vs split sub rows | 5632800/5632800 | Direct profile covers only sub-DTF direct calls, not normal calls. |
| G3_profile_coverage | PASS | direct profile total / split dft_us | 0.984943 | Direct profile should explain most split dft_us; the remainder includes normal-call DFT and timer overhead. |
| G4_internal_accounting | PASS | (digit+ifft)/direct_total | 0.986263 | Digit and ifft timers should account for the direct profile block. |
| G5_dominant_subcomponent | RECORDED | dominant | ifft | Selects the next candidate family. |
| G6_claim_boundary | PASS_PROFILE_ONLY | scope | instrumented one-run profile | Do not use Stage307 latency as final speed evidence. |
| G7_decision | PASS_STAGE307_DIRECT_IFFT_LIFECYCLE_PROFILE_RECORDED | stage decision | PASS_STAGE307_DIRECT_IFFT_LIFECYCLE_PROFILE_RECORDED | Controls Stage308 route. |
