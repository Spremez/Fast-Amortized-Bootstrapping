# Stage145 r4-Unrolled Policy Audit

Date: 2026-07-03

## Decision

`WEAK_STAGE145_POLICY_KEEP_EXPLICIT_DO_NOT_PROMOTE`

## Gates

| gate | status | metric | value | detail |
| --- | --- | --- | --- | --- |
| stage145_precondition | PASS | stage144_inputs | summary;perf | Stage145 reads Stage144 gate outputs. |
| stage145_default_guard | PASS | default_policy | KEEP_DEFAULT_UNCHANGED_EXPLICIT_EXPERIMENT_ONLY | No default/scalar path change is authorized. |
| stage145_claim_guard | WEAK_STAGE145_POLICY_KEEP_EXPLICIT_DO_NOT_PROMOTE | claim_policy | DISALLOW_FINAL_SPEEDUP_CLAIM_ALLOW_NEGATIVE_ABLATION | Promotion wording follows Stage144 evidence strength. |

## Policy

| input_stage | stage144_perf_status | stage144_noise_status | stage144_resource_status | mean_speedup | min_speedup | ci95_low | ci95_high | default_path_policy | claim_policy | next_research_action | decision |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Stage144 | WEAK_STAGE144_PERF_POSITIVE_BUT_CI_CROSSES_ONE | PASS | PASS | 1.000249 | 0.924113 | 0.835834 | 1.164664 | KEEP_DEFAULT_UNCHANGED_EXPLICIT_EXPERIMENT_ONLY | DISALLOW_FINAL_SPEEDUP_CLAIM_ALLOW_NEGATIVE_ABLATION | Stage146 should attribute variance or route to another algorithmic candidate. | WEAK_STAGE145_POLICY_KEEP_EXPLICIT_DO_NOT_PROMOTE |

## Interpretation

The r4-unrolled AVX512 path remains useful as an ablation and variance target, but Stage144 does not justify default promotion or final SAB speedup wording.
