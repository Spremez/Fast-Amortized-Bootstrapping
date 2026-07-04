# Stage266 Current-Head Non-Binary Native Counter Gate

Decision: `PASS_STAGE266_NATIVE_COUNTER_HANDOFF_READY_AUTH_REQUIRED`.

Stage266 creates and, when runtime remote credentials are supplied, executes a
native perf gate for the current non-binary PVW/MAT-SAB path. The measured
target is r=4 include-zero and ternary full SAB with primary metric
`T_bootstrap/r`. This stage does not change SAB code.

## Tool Matrix

| tool_or_route | status | claim_effect |
| --- | --- | --- |
| stage265_precondition | present | Stage266 starts only after Stage265 selected fresh current-head counters. |
| local_perf | missing | Local WSL can run smoke but cannot provide native counter attribution when perf is missing. |
| local_auth_helper | available | Runtime remote execution is possible only if a secret is supplied externally. |
| remote_batch_auth | auth_required | If batch auth is unavailable and no runtime secret is provided, Stage266 remains a handoff gate. |
| runtime_secret | not_provided | No secret is written to repo artifacts. |

## Run Metrics

| mode | correctness | r | pvw_avg_us | scalar_repeated_avg_us | speedup_vs_scalar_repeated | t_bootstrap_over_r_pvw_us | t_bootstrap_over_r_scalar_us |
| --- | --- | --- | --- | --- | --- | --- | --- |

## Counter Summary

| mode | cycles | instructions | loads | stores | fp512 | ipc | load_store_per_cycle | load_store_to_fp512 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |

## Proof Gate

| gate | status | metric | value | interpretation |
| --- | --- | --- | --- | --- |
| G1_stage265_precondition | PASS | stage265 proof | present | Stage266 follows Stage265 refresh-required decision. |
| G2_local_probe | RECORDED | local_perf | missing | Current WSL probe records whether local hardware counters are usable. |
| G3_remote_auth_probe | RECORDED | remote_batch_auth | auth_required | Batch auth probe uses no stored secret. |
| G4_runtime_secret_policy | PASS_NO_SECRET_STORED | runtime_secret | not_provided | Remote execution uses runtime env only; no secret is committed. |
| G5_native_results | HANDOFF_ONLY | run_rows/counter_rows | 0/0 | Native results are required before hardware-counter claims can be upgraded. |
| G6_decision | PASS_STAGE266_NATIVE_COUNTER_HANDOFF_READY_AUTH_REQUIRED | stage decision | PASS_STAGE266_NATIVE_COUNTER_HANDOFF_READY_AUTH_REQUIRED | Stage266 either records native counters or a reproducible handoff gate. |

## Claim Boundary

| claim | status | allowed_wording | forbidden_wording |
| --- | --- | --- | --- |
| current_nonbinary_native_counter_attribution | not_yet_supported | Use Stage266 counters only if G6 records native counters. | Use the handoff-only gate as counter evidence. |
| current_nonbinary_t_bootstrap_over_r | unchanged_stage262_263 | Stage262/263 remain the current WSL timing/profile evidence. | Treat Stage266 handoff as a new speedup measurement. |
| secret_handling | no_secret_stored | Runtime secret, if used, is supplied via environment and scrubbed from logs. | Commit credentials or secret-bearing command lines. |

## Next Queue

| priority | route | entry_condition | status | gate |
| --- | --- | --- | --- | --- |
| P0 | stage267_counter_interpretation_or_local_fallback | Stage266 native counters recorded, or handoff remains auth-required. | fallback_or_wait_runtime_secret | Do not implement hot-path code until counter/profile evidence identifies a concrete mechanism. |
| P1 | stage267_local_split_projection | No native counters, local WSL only. | available | Projection only, no hardware-counter claim. |
