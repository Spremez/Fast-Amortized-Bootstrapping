# Stage191 Secret-Correction Noise/Resource Gate

Decision: `PASS_STAGE191_T4_SECRET_CORRECTION_LOWER_BOUND_RECORDED_IMPLEMENTATION_DENIED`.

Stage191 targets the Stage187 `T4_noise_bound` obligation for the only
remaining closure family after Stage189/190: use secret-dependent correction,
key switching, or re-sharing to turn lane-local compact masks into a one-mask
PVW_TMLWE state.

This is a lower-bound gate, not a production implementation. It records the
latency budget, key/materialization budget, and normalized noise sensitivity
that any future correction route must beat before touching `sab_pvw_*`.

Current exact full-MAT complete-SAB evidence remains scoped:

- `T_bootstrap/r` mean speedup versus repeated scalar:
  `1.131666667x`;
- conservative min: `1.115000000x`;
- CI-low: `1.095041982x`.

## Gate Summary

| gate | status | metric | value | evidence | detail | next_action |
| --- | --- | --- | --- | --- | --- | --- |
| stage191_inputs | PASS | required_inputs_present | 1 | repro/stage189_closed_state_linear_probe/conversion_cost_model.csv; repro/stage190_selector_distribution_distinguisher/distribution_route.csv; repro/stage138_shared_mask_compact_gate/ratio_summary.csv | Stage191 targets T4 after T2 public closure and T1 standard-distribution shortcuts were rejected. | Repair missing inputs before interpreting the lower-bound gate. |
| stage191_latency_budget | RECORDED_TIGHT_BUDGET | proxy_rows_failing_decomp_dft_addmul_budget | 5 | repro/stage191_secret_correction_noise_resource_gate/latency_budget.csv | Secret correction must fit inside saved compact-kernel time; proxy rows fail when correction needs decompose/DFT plus addmul. | No implementation unless an isolated correction kernel is measured below budget. |
| stage191_resource_budget | RECORDED | ks_like_count_negative_rows | 3 | repro/stage191_secret_correction_noise_resource_gate/resource_budget.csv | Minimal one-gadget correction can preserve row-count gain, but KS-like T-gadget correction can erase it for some r. | Require explicit key format before code. |
| stage191_noise_sensitivity | T4_NOT_PROVEN | nonzero_noise_rows_require_bound | 12 | repro/stage191_secret_correction_noise_resource_gate/noise_sensitivity.csv | Any nonzero correction noise increases normalized per-step variance; no measured recurrence or multi-seed bound exists. | Run only isolated noise recurrence proof/probe if this route is continued. |
| stage191_decision | PASS_STAGE191_T4_SECRET_CORRECTION_LOWER_BOUND_RECORDED_IMPLEMENTATION_DENIED | production_compact_sab_permission | 0 | repro/stage191_secret_correction_noise_resource_gate/route_decision.csv | Secret-correction/key-switch closure remains proof-only and implementation-denied. | Proceed to a structured-key proof draft or keep compact route as limitation. |

## Latency Budget

| backend | r | N | kernel_repeated_us | kernel_shared_us | available_saved_us | min_corrections_per_cmux | budget_us_per_correction | proxy_addmul_us_per_lane | proxy_decomp_dft_addmul_us_per_lane | addmul_proxy_over_budget | decomp_dft_addmul_proxy_over_budget | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| spqlios | 2 | 1024 | 54.052910 | 45.971770 | 8.081140 | 1 | 8.081140 | 8.575000 | 19.795700 | 1.061113 | 2.449617 | FAIL_IF_CORRECTION_NEEDS_DECOMP_DFT_PLUS_ADDMUL |
| spqlios | 2 | 512 | 35.046830 | 25.241840 | 9.804990 | 1 | 9.804990 | 3.489816 | 8.476116 | 0.355922 | 0.864470 | LATENCY_BUDGET_ONLY_FOR_ADDMUL_LIKE_CORRECTION |
| spqlios | 4 | 1024 | 141.960810 | 95.200210 | 46.760600 | 3 | 15.586867 | 13.293033 | 23.428983 | 0.852836 | 1.503123 | FAIL_IF_CORRECTION_NEEDS_DECOMP_DFT_PLUS_ADDMUL |
| spqlios | 4 | 512 | 52.381410 | 40.480820 | 11.900590 | 3 | 3.966863 | 5.823283 | 10.082800 | 1.467982 | 2.541756 | FAIL_IF_CORRECTION_NEEDS_DECOMP_DFT_PLUS_ADDMUL |
| spqlios | 6 | 1024 | 166.776730 | 118.331630 | 48.445100 | 5 | 9.689020 | 15.944700 | 25.280200 | 1.645646 | 2.609160 | FAIL_IF_CORRECTION_NEEDS_DECOMP_DFT_PLUS_ADDMUL |
| spqlios | 6 | 512 | 79.255430 | 58.457670 | 20.797760 | 5 | 4.159552 | 7.397611 | 11.425856 | 1.778463 | 2.746896 | FAIL_IF_CORRECTION_NEEDS_DECOMP_DFT_PLUS_ADDMUL |

## Resource Budget

| r | N | T | dense_selector_rows | compact_selector_rows | max_extra_rows_before_losing_count_gain | minimal_one_gadget_correction_rows | ks_like_T_gadget_correction_rows | dense_over_compact_plus_minimal | dense_over_compact_plus_ks_like | minimal_status | ks_like_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2 | 2048 | 7 | 63 | 56 | 7 | 7 | 49 | 1.000000 | 0.600000 | COUNT_POSITIVE | COUNT_NEGATIVE |
| 4 | 2048 | 7 | 175 | 112 | 63 | 21 | 147 | 1.315789 | 0.675676 | COUNT_POSITIVE | COUNT_NEGATIVE |
| 6 | 2048 | 7 | 343 | 168 | 175 | 35 | 245 | 1.689655 | 0.830508 | COUNT_POSITIVE | COUNT_NEGATIVE |

## Noise Sensitivity

| r | cmux_steps_binary_set_2_3_2048 | min_corrections_per_cmux | rho_sigma_correction_over_baseline_step | per_step_sigma_multiplier | variance_multiplier | status | interpretation |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2 | 573440 | 1 | 0.00 | 1.000000 | 1.000000 | ZERO_EXTRA_NOISE_ONLY | Normalized sensitivity; not a measured noise proof. |
| 2 | 573440 | 1 | 0.10 | 1.004988 | 1.010000 | T4_NEEDS_REAL_NOISE_BOUND | Normalized sensitivity; not a measured noise proof. |
| 2 | 573440 | 1 | 0.25 | 1.030776 | 1.062500 | T4_NEEDS_REAL_NOISE_BOUND | Normalized sensitivity; not a measured noise proof. |
| 2 | 573440 | 1 | 0.50 | 1.118034 | 1.250000 | T4_NEEDS_REAL_NOISE_BOUND | Normalized sensitivity; not a measured noise proof. |
| 2 | 573440 | 1 | 1.00 | 1.414214 | 2.000000 | T4_NEEDS_REAL_NOISE_BOUND | Normalized sensitivity; not a measured noise proof. |
| 4 | 573440 | 3 | 0.00 | 1.000000 | 1.000000 | ZERO_EXTRA_NOISE_ONLY | Normalized sensitivity; not a measured noise proof. |
| 4 | 573440 | 3 | 0.10 | 1.014889 | 1.030000 | T4_NEEDS_REAL_NOISE_BOUND | Normalized sensitivity; not a measured noise proof. |
| 4 | 573440 | 3 | 0.25 | 1.089725 | 1.187500 | T4_NEEDS_REAL_NOISE_BOUND | Normalized sensitivity; not a measured noise proof. |
| 4 | 573440 | 3 | 0.50 | 1.322876 | 1.750000 | T4_NEEDS_REAL_NOISE_BOUND | Normalized sensitivity; not a measured noise proof. |
| 4 | 573440 | 3 | 1.00 | 2.000000 | 4.000000 | T4_NEEDS_REAL_NOISE_BOUND | Normalized sensitivity; not a measured noise proof. |
| 6 | 573440 | 5 | 0.00 | 1.000000 | 1.000000 | ZERO_EXTRA_NOISE_ONLY | Normalized sensitivity; not a measured noise proof. |
| 6 | 573440 | 5 | 0.10 | 1.024695 | 1.050000 | T4_NEEDS_REAL_NOISE_BOUND | Normalized sensitivity; not a measured noise proof. |
| 6 | 573440 | 5 | 0.25 | 1.145644 | 1.312500 | T4_NEEDS_REAL_NOISE_BOUND | Normalized sensitivity; not a measured noise proof. |
| 6 | 573440 | 5 | 0.50 | 1.500000 | 2.250000 | T4_NEEDS_REAL_NOISE_BOUND | Normalized sensitivity; not a measured noise proof. |
| 6 | 573440 | 5 | 1.00 | 2.449490 | 6.000000 | T4_NEEDS_REAL_NOISE_BOUND | Normalized sensitivity; not a measured noise proof. |

## Route Decision

| route | t4_status | latency_status | noise_status | implementation_permission | next_action |
| --- | --- | --- | --- | --- | --- |
| public_projection_to_shared_mask | NOT_APPLICABLE_REJECTED_BY_T2 | no correction benchmark because algebra gate failed | not evaluated | NO | closed by Stage189 unless a new algebraic invariant appears |
| secret_correction_each_cmux | OPEN_BLOCKED_BY_NO_NOISE_PROOF | budget is tight and fails if correction requires decompose/DFT plus addmul in proxy rows | any nonzero correction noise increases per-step variance; no multi-seed bound exists | NO | only an isolated noise/key-size proof probe, not sab_pvw hot-path code |
| keyswitch_or_reshare_each_cmux | OPEN_HIGH_RISK | must fit within per-correction saved-us budget and include key/materialization overhead | requires KS noise recurrence over all CMUX steps | NO | derive explicit KS parameters and compare against budget before code |
| dense_full_mat_reexpansion | CURRENT_REFERENCE | implemented exact path; no compact claim | covered by current exact PVW/MAT-SAB gates | YES_FOR_EXACT_FULL_MAT_ONLY | keep as baseline/reference |
| new_structured_selector_distribution | PROOF_ONLY_AFTER_T1 | unmeasured | must prove selector and repeated SAB noise recurrence | NO | first supply a T1 structured-key assumption/reduction |
