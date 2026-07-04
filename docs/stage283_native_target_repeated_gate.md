# Stage283 Native Target Repeated Gate

Decision: `PASS_STAGE283_NATIVE_ACCESS_MISSING_HANDOFF_READY`.

Stage283 is the native target-parameter gate for the selected
`backend_sub_decomp_dual` CMUX residual path. It uses `T_bootstrap/r` as the
primary endpoint and does not convert WSL results into native evidence.

## Native Access

| status | host | user | auth_mode | reason |
| --- | --- | --- | --- | --- |
| failed | 192.168.107.220 | delld | BatchMode | native_access_failed_or_missing_auth |

## Latency Summary

| variant | reps | correctness | mean T/r us | scalar speedup mean | speedup vs fast control |
| --- | ---: | --- | ---: | ---: | ---: |
| fast_control | 0 | missing |  |  |  |
| backend_sub_decomp_dual | 0 | missing |  |  |  |
| comparison | 0 | missing_or_fail |  |  |  |

## Proof Gate

| gate | status | metric | value | interpretation |
| --- | --- | --- | --- | --- |
| G1_access | PASS_RECORDED_MISSING | native access | native_access_failed_or_missing_auth | Native evidence is allowed only when access succeeds. |
| G2_remote_env | MISSING | remote env rows | 0 | CPU/backend provenance for native runs. |
| G3_correctness | MISSING_OR_FAIL | correctness | missing/missing | Timing is interpreted only after both native variants pass. |
| G4_repeated_speed | MISSING_OR_NEUTRAL | candidate/control mean | missing | Native target repeated T_bootstrap/r speedup. |
| G5_decision | PASS_STAGE283_NATIVE_ACCESS_MISSING_HANDOFF_READY | stage decision | PASS_STAGE283_NATIVE_ACCESS_MISSING_HANDOFF_READY | No native performance claim if access is missing. |

Generated from input head `4bd3d04`.
