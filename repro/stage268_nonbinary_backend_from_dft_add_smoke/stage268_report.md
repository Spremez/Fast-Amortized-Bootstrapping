# Stage268 Non-Binary Backend FromDFT-add Smoke

Decision: `PASS_STAGE268_BACKEND_FROM_DFT_ADD_SMOKE_POSITIVE_REPEAT_REQUIRED`.

Stage268 is the bounded screening gate selected by Stage267. It compares the
existing explicit `SAB_PVW_BACKEND_FROM_DFT_ADD=true` route against default
PVW/MAT-SAB for r=4 include-zero and ternary. The primary metric is the
amortized per-body metric requested for MAT-RLWE:

```text
T_bootstrap / r
```

## Variant Comparison

| mode | r | default_t_bootstrap_over_r_us | backend_t_bootstrap_over_r_us | backend_speedup_vs_default | backend_delta_pct | status |
| --- | --- | --- | --- | --- | --- | --- |
| include_zero | 4 | 7897620.750 | 7612585.750 | 1.037443 | -3.609 | positive |
| ternary | 4 | 7892451.500 | 7778112.750 | 1.014700 | -1.449 | positive |

## Bench Summary

| variant | mode | r | reps | correctness_gate | t_bootstrap_over_r_pvw_us | speedup_vs_scalar_repeated | log |
| --- | --- | --- | --- | --- | --- | --- | --- |
| backend_from_dft_add | include_zero | 4 | 1 | Pass | 7612585.750 | 1.393 | repro/stage268_nonbinary_backend_from_dft_add_smoke/raw/backend_from_dft_add_include_zero_r4_reps1_run.log |
| default | include_zero | 4 | 1 | Pass | 7897620.750 | 1.357 | repro/stage268_nonbinary_backend_from_dft_add_smoke/raw/default_include_zero_r4_reps1_run.log |
| backend_from_dft_add | ternary | 4 | 1 | Pass | 7778112.750 | 1.372 | repro/stage268_nonbinary_backend_from_dft_add_smoke/raw/backend_from_dft_add_ternary_r4_reps1_run.log |
| default | ternary | 4 | 1 | Pass | 7892451.500 | 1.353 | repro/stage268_nonbinary_backend_from_dft_add_smoke/raw/default_ternary_r4_reps1_run.log |

## Proof Gate

| gate | status | metric | value | interpretation |
| --- | --- | --- | --- | --- |
| G1_coverage | PASS | variant/mode coverage | backend_from_dft_add:include_zero,default:include_zero,backend_from_dft_add:ternary,default:ternary | Covers default and backend FromDFT-add for r=4 include-zero and ternary. |
| G2_correctness | PASS | PVW/scalar target correctness | 4/4 | Correctness must pass before interpreting timing. |
| G3_primary_metric | PASS | T_bootstrap/r | backend_vs_default_same_backend | Smoke compares PVW/MAT variants on the requested amortized per-body metric. |
| G4_smoke_threshold | PASS | minimum backend speedup vs default | 1.014700x | Single-run smoke requires both modes above 1.01x before repeated/noise/resource promotion. |
| G5_claim_boundary | PASS_SMOKE_ONLY | no final speedup claim | single_run | Stage268 is a screening gate, not final evidence. |
| G6_decision | PASS_STAGE268_BACKEND_FROM_DFT_ADD_SMOKE_POSITIVE_REPEAT_REQUIRED | stage decision | PASS_STAGE268_BACKEND_FROM_DFT_ADD_SMOKE_POSITIVE_REPEAT_REQUIRED | Promotion requires a positive smoke; neutral results close this local materialization candidate. |

## Claim Boundary

| claim | status | allowed_wording | forbidden_wording |
| --- | --- | --- | --- |
| backend_from_dft_add_smoke | smoke_positive | Stage268 screens the existing explicit backend FromDFT-add flag against default PVW/MAT-SAB using T_bootstrap/r. | Stage268 proves final complete SAB speedup. |
| algorithm_speedup_vs_scalar_sab | not_remeasured_here | Scalar-repeated numbers in each row remain context; the Stage268 primary comparison is backend PVW/MAT vs default PVW/MAT. | Mix backend flag deltas with historical scalar-repeated speedup as one claim. |
| hot_path_change | no_new_hot_path_code | Stage268 uses an existing explicit flag only. | Stage268 introduced a new SAB/MAT algorithm. |

## Next Queue

| priority | route | entry_condition | gate | status | failure_action |
| --- | --- | --- | --- | --- | --- |
| P0 | stage269_backend_from_dft_add_repeated_noise_resource | Stage268 positive smoke for both non-binary modes. | repeated T_bootstrap/r, noise/resource, same backend. | selected | If repeated rows lose benefit, demote Stage268 to smoke-only. |
| P1 | stage270_counter_attribution | Repeated rows positive. | native counters or proxy-labeled assembly audit. | conditional | No hardware claim without counters. |

Generated from input head `dc0324b`.
