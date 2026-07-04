# Stage281 CMUX Residual Repeated Gate

Decision: `PASS_STAGE281_REPEATED_POSITIVE_NOISE_RESOURCE_REQUIRED`.

Stage281 repeats the Stage280 selected candidate
`backend_sub_decomp_dual` against the guarded include-zero fast control.
The metric is unprofiled complete SAB `T_bootstrap/r`.

## Latency Summary

| variant | reps | correctness | mean T/r us | min T/r us | max T/r us | scalar speedup mean |
| --- | ---: | --- | ---: | ---: | ---: | ---: |
| fast_control | 3 | Pass | 7058774.917 | 7021762.250 | 7097621.000 | 1.495361 |
| backend_sub_decomp_dual | 3 | Pass | 6584179.750 | 6555921.500 | 6603151.500 | 1.596038 |

Mean speedup vs fast control: `1.072081`.
Conservative `control_min / candidate_max`: `1.063396`.

## Proof Gate

| gate | status | metric | value | interpretation |
| --- | --- | --- | --- | --- |
| G1_input | PASS | input commit | 8ec1db9 | Stage281 starts after Stage280 candidate selection. |
| G2_correctness | PASS | latency correctness | Pass/Pass | Timing is interpreted only after both variants pass. |
| G3_repeated_mean | PASS | candidate speedup vs fast_control mean | 1.072081 | Repeated mean uses unprofiled full SAB T_bootstrap/r. |
| G4_conservative_bound | PASS_STRONG | control_min/candidate_max | 1.063396 | Conservative overlap check; not required for screen promotion but recorded. |
| G5_profile_refresh | PASS | profile rows | 20 | Profile remains attribution-only. |
| G6_decision | PASS_STAGE281_REPEATED_POSITIVE_NOISE_RESOURCE_REQUIRED | stage decision | PASS_STAGE281_REPEATED_POSITIVE_NOISE_RESOURCE_REQUIRED | Positive repeated result still needs noise/resource and native gates before final claims. |

## Claim Boundary

This is a repeated local gate, not a final paper claim. Noise/resource and
native execution remain separate gates.

Generated from input head `8ec1db9`.
