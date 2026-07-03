# Stage139 Compact Closure Audit

Date: 2026-07-03

## Decision

`PASS_STAGE139_COMPACT_DIAGONAL_NOT_PVW_CLOSED_REDIRECT_FULL_MAT_ROUTE`

Stage139 prevents a route error: Stage138's compact diagonal kernel improves amortized independent-lane EP, but its output is not directly a PVW_TMLWE accumulator if lane masks differ.

## Gates

| gate | status | metric | value | detail |
|---|---|---|---|---|
| stage139_mosfhet_static_build | PASS | make_static_spqlios_pvw | true | MOSFHET static build with PVW/MAT objects. |
| stage139_probe_compile | PASS | gcc_probe_compile | true | Standalone compact closure audit compiled. |
| stage139_probe_run | PASS | probe_returncode | 0 | Compact closure audit executed. |
| stage139_closure_rows | PASS | closure_rows | 6 | Closure rows recorded for r=2,4,6 and N=512,1024. |
| stage139_expected_nonclosure | PASS | min_mask_mismatches | 512.000000 | Compact diagonal output has lane-specific masks and is not directly PVW_TMLWE closed. |
| stage139_decision | PASS_STAGE139_COMPACT_DIAGONAL_NOT_PVW_CLOSED_REDIRECT_FULL_MAT_ROUTE | route_policy |  | Stage139 decides whether Stage138 compact output can be direct SAB state. |

## Closure Rows

| backend | r | N | T | Bg_bit | seed | mask_mismatches | max_mask_gap | status |
|---|---|---|---|---|---|---|---|---|
| spqlios | 2 | 512 | 7 | 7 | 0 | 512 | 1162068678945864163524608.000000000 | EXPECTED_NONCLOSED_COMPACT_OUTPUT |
| spqlios | 4 | 512 | 7 | 7 | 0 | 1536 | 1329579791263764056113152.000000000 | EXPECTED_NONCLOSED_COMPACT_OUTPUT |
| spqlios | 6 | 512 | 7 | 7 | 0 | 2560 | 1375229237205484026462208.000000000 | EXPECTED_NONCLOSED_COMPACT_OUTPUT |
| spqlios | 2 | 1024 | 7 | 7 | 0 | 1024 | 2905355668607332614406144.000000000 | EXPECTED_NONCLOSED_COMPACT_OUTPUT |
| spqlios | 4 | 1024 | 7 | 7 | 0 | 3072 | 2905355668607332614406144.000000000 | EXPECTED_NONCLOSED_COMPACT_OUTPUT |
| spqlios | 6 | 1024 | 7 | 7 | 0 | 5120 | 2905355668607332614406144.000000000 | EXPECTED_NONCLOSED_COMPACT_OUTPUT |
