# Stage279 Native Access and Residual Profile

Decision: `PASS_STAGE279_NATIVE_ACCESS_MISSING_PROFILE_SELECT_RESIDUAL`.

Stage279 records native access status with SSH BatchMode and measures the
default-vs-fast include-zero residual profile under `spqlios_avx512`.

## Native Access

| status | host | user | auth_mode | exit_code | reason |
| --- | --- | --- | --- | --- | --- |
| failed | 192.168.107.220 | delld | BatchMode | 255 | ssh_batchmode_access_failed |

## Profile Compare

| mode | r | default_t_bootstrap_over_r_us | fast_t_bootstrap_over_r_us | fast_speedup_vs_profile_default | default_sub_a_us | fast_sub_a_us | sub_a_reduction_ratio | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| include_zero | 4 | 7764513.750 | 7088330.000 | 1.095394 | 3364257.000 | 654392.000 | 5.141042 | positive |

## Top Residual Components

| component | component_us | calls | share_of_body | share_of_pvw |
| --- | --- | --- | --- | --- |
| rgsw_monomial | 27413204.000 | 40 | 0.976161 | 0.966843 |
| cmux_total | 27214770.000 | 573440 | 0.969095 | 0.959844 |
| mat_ep | 12827058.000 | 573440 | 0.456761 | 0.452401 |
| cmux_from_dft | 6401719.000 | 573440 | 0.227960 | 0.225784 |
| cmux_add | 3982495.000 | 573440 | 0.141813 | 0.140460 |
| cmux_sub | 3906004.000 | 573440 | 0.139090 | 0.137762 |
| sub_a_total | 654392.000 | 39 | 0.023302 | 0.023080 |
| sub_a_rotate | 530520.000 | 79872 | 0.018891 | 0.018711 |
| ncmux_total | 422829.000 | 5080 | 0.015057 | 0.014913 |
| ncmux_auto | 166937.000 | 5080 | 0.005944 | 0.005888 |

## Proof Gate

| gate | status | metric | value | interpretation |
| --- | --- | --- | --- | --- |
| G1_native_probe | PASS_RECORDED | BatchMode access | failed | Native access status is recorded without credentials. |
| G2_profile_coverage | PASS | profile variants | default,include_zero_coeff_one_fast | Residual profile compares default and fast include-zero variants. |
| G3_correctness | PASS | profile correctness | 2/2 | Profile timing is interpreted only after correctness passes. |
| G4_local_speed | PASS | profile fast speedup | 1.095394 | Body-profile run should still show fast path benefit. |
| G5_residual_selection | PASS | top residual component | rgsw_monomial:0.966843 | Next algorithm candidate must target the measured residual, not pre-fast assumptions. |
| G6_claim_boundary | PASS_NOT_FINAL | claim scope | PASS_STAGE279_NATIVE_ACCESS_MISSING_PROFILE_SELECT_RESIDUAL | Native paper-grade claim remains gated; residual profile selects next engineering candidate. |
| G7_decision | PASS_STAGE279_NATIVE_ACCESS_MISSING_PROFILE_SELECT_RESIDUAL | stage decision | PASS_STAGE279_NATIVE_ACCESS_MISSING_PROFILE_SELECT_RESIDUAL | Proceed to residual-driven next candidate and/or native access resolution. |

## Claim Boundary

| claim | status | allowed_wording | forbidden_wording |
| --- | --- | --- | --- |
| native_access | recorded | Stage279 records BatchMode native access status without storing credentials. | Native performance evidence exists if only the access probe failed. |
| residual_profile | measured | Stage279 selects next candidates from the measured fast-path residual profile. | Stage279 proves final algorithm optimality. |
| include_zero_fast | still_guarded | Fast path remains scoped to current PVW include-zero coefficient-one semantics. | The optimization covers ternary or general scalar include-zero. |

## Next Queue

| priority | route | entry_condition | gate | status | failure_action |
| --- | --- | --- | --- | --- | --- |
| P0 | stage280_cmux_mat_ep_residual_optimization_design | Top residual component is rgsw_monomial. | Design a falsifiable CMUX/MAT-EP residual candidate under fast flag; require microbench and full SAB A/B. | selected | No next optimization without full SAB A/B. |
| P1 | stage281_native_execution_resolution | Native probe status is failed. | Resolve key-based native access or keep claim local-only. | conditional | Do not claim native performance. |

Generated from input head `32d9478`.
