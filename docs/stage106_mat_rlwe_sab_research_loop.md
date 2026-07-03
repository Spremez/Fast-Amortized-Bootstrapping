# Stage106 MAT-RLWE SAB Research Loop

Date: 2026-07-03

## Decision

`PASS_STAGE106_RESEARCH_LOOP_FIXED_OPTIMALITY_OPEN`

Stage106 reframes PVW/MAT-SAB as an algorithmic MAT-RLWE SAB
research program. The primary endpoint is complete-SAB latency
amortized over processed lanes/bits:

```text
A_mat(r) = T_mat_complete_bootstrap(r) / r
```

The existing r=2/r=4 complete-SAB speedups remain valid under this
endpoint because the compared runs process the same number of lanes.
Theoretical optimality is explicitly left open.

## Summary

| gate | status | detail |
|---|---|---|
| stage106_primary_endpoint | PASS | Primary endpoint is amortized complete-SAB latency per processed lane/bit: T_total/r. |
| stage106_existing_evidence_reinterpreted | PASS | Existing r=2/r=4 speedups are same-r total-time speedups and therefore equal per-lane amortized speedups. |
| stage106_theoretical_optimality_boundary | OPEN_NOT_PROVEN | The MAT-RLWE SAB optimality claim remains open until lower-bound gap and implementation counters are closed. |
| stage106_decision | PASS_STAGE106_RESEARCH_LOOP_FIXED_OPTIMALITY_OPEN | Research loop is fixed; existing evidence is usable for amortized improvement, but theoretical optimality is not yet proven. |

## Amortized Evidence

| source | r | samples | PVW total s | scalar total s | PVW per lane s | scalar per lane s | speedup | status |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| stage36_target_r2_10run | 2 | 10 | 14.665117 | 17.315264 | 7.332558 | 8.657632 | 1.191 | PASS_TARGET_PERF_10RUN |
| stage36_target_r4_10run | 4 | 10 | 27.556959 | 37.958531 | 6.889240 | 9.489633 | 1.377 | PASS_TARGET_PERF_10RUN |
| stage88_h14_backend_r6_3run | 6 | 3 | 38.368030 | 55.137541 | 6.394672 | 9.189590 | 1.437 | CANDIDATE_EXPLICIT_NOT_DEFAULT |

## Theory Model

| id | object | formula | status | next check |
|---|---|---|---|---|
| M1 | scalar repeated SAB | `T_scalar_repeat(r)=r*((h+1)*rho*N*C_scalar_cmux+T_tail_scalar)` | FORMAL_MODEL_BASELINE | keep same backend and same processed lane count for every comparison |
| M2 | MAT-RLWE SAB schedule | `T_mat(r)=(h+1)*rho*N*C_mat_cmux(r)+T_tail_mat(r)` | FORMAL_MODEL_TO_REFINE | measure C_mat_cmux(r) decomposition into DFT/FMA/load/store/fromDFT/body-add |
| M3 | amortized primary endpoint | `A_mat(r)=T_mat(r)/r; improvement=A_scalar_repeat(r)/A_mat(r)` | PRIMARY_ENDPOINT_FIXED | all future tables must report total time and per-lane time |
| M4 | optimality lower-bound gap | `gap(r)=A_impl(r)/A_lower_bound(r), where bound separates shared schedule and unavoidable body work` | THEORY_GAP_OPEN_NOT_A_RESULT | derive lower bound from memory/FMA counts and validate with assembly/perf counters |
| M5 | dense MAT risk | `if C_mat_cmux(r) grows like r^2, A_mat(r) can stop improving despite schedule sharing` | RISK_TO_TEST | compare body-linear, tiled, and dense MAT kernels under same SAB schedule |

## Research Gates

| gate | status | decision | stop rule |
|---|---|---|---|
| G1_primary_metric_reframed | PASS | Use T_total/r as the primary endpoint for MAT-RLWE SAB. | Reject any future speedup table that omits per-lane time. |
| G2_existing_r2_r4_amortized_support | PASS | Existing complete-SAB data supports amortized improvement for r=2/r=4. | Rerun Stage36 if target parameters, backend, or benchmark harness changes. |
| G3_r6_candidate_support | CANDIDATE_ONLY | H14 r=6 backend path is a candidate, not a high-stat optimality result. | Do not promote r=6 to paper-level optimality without 10+ runs and model-gap analysis. |
| G4_correctness_noise_resource_guard | PASS_CANDIDATE_GUARD | r=6 candidate has smoke-scale noise/resource support only. | Any new variant needs deterministic equivalence, multi-seed noise, and resource tables before speedup claims. |
| G5_counter_model_not_optimality | PASS_ATTRIBUTION_ONLY | Hardware counters exist for attribution but do not close theoretical optimality. | Stop theoretical-optimality wording until load/store/FMA lower bound and assembly audit are recorded. |
| G6_no_theory_loop_rule | PASS_PROCESS_GATE | Every theory item must name the next experiment or be demoted to background. | After two theory-only iterations without a runnable gate, freeze the hypothesis and run measurement. |
| G7_stage105_precondition | PASS | Stage106 starts from the closed scoped package and reopens only the optimality research question. | Do not reinterpret old evidence if Stage105 is not passing. |

## Candidate Variants

| id | name | status | next experiment |
|---|---|---|---|
| V106-A | current_active_buffer_pvw_mat_sab | BASELINE_FOR_NEW_RESEARCH_LOOP | keep as baseline for all future MAT-RLWE optimality variants |
| V106-B | body_linear_mat_external_product | HYPOTHESIS_THEORY_AND_KERNEL_GATE_REQUIRED | microbench r=2/4/6/8 plus full SAB A/B under same schedule |
| V106-C | dfT_lazy_schedule_window | HYPOTHESIS_SCHEDULE_GATE_REQUIRED | single-window equivalence, then full sparse_mul correctness and profile |
| V106-D | body_major_coefficient_blocked_layout | HYPOTHESIS_LAYOUT_GATE_REQUIRED | layout-only kernel microbench; do not change key format until positive |
| V106-E | r_adaptive_tile_policy | HYPOTHESIS_POLICY_GATE_REQUIRED | r sweep with the same gates and resource thresholds |

## Non-Drift Rule

Do not promote a theory claim unless it has a named experiment and a
recorded result. After two theory-only iterations without a runnable gate,
freeze the hypothesis and run the closest microbench or complete-SAB A/B.
