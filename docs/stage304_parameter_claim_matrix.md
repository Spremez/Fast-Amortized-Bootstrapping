# Stage304 Parameter Claim Matrix

Decision: `PASS_STAGE304_TWO_PARAMETER_LOCAL_GENERALIZATION_WITH_COUNTER_MECHANISM`.

Stage304 combines the two high-stat local complete-SAB campaigns with the current-head native counter mechanism evidence.

## Parameter Evidence

| param | samples | direct_over_selected_control | direct_over_repeated_scalar | noise_trials | pair_failures | ci_separated |
| --- | --- | --- | --- | --- | --- | --- |
| SET_2_3_2048 | 10 | 1.075398 | 1.735849 | 10 | 0 | true |
| SET_4_5_2048 | 10 | 1.070458 | 1.731986 | 10 | 0 | true |

## Mechanism Bridge

| metric | value | interpretation |
| --- | --- | --- |
| native_t_over_r_selected_over_direct | 1.134934244 | Stage301 one-run native latency direction agrees with local high-stat direction. |
| cycles_selected_over_direct | 1.045496632 | Direct DFT records fewer cycles than selected-control in Stage301. |
| instructions_selected_over_direct | 1.024950663 | Direct DFT records fewer instructions, supporting materialization-wrapper removal. |
| loads_selected_over_direct | 1.038873490 | Direct DFT records fewer loads. |
| stores_selected_over_direct | 1.019831601 | Direct DFT records fewer stores. |
| fp512_selected_over_direct | 1.000243246 | AVX512 FP arithmetic is neutral; this is not an arithmetic-volume reduction claim. |
| stage302_decision | PASS_STAGE302_COUNTER_SUPPORTS_MEMORY_INSTRUCTION_MECHANISM | Stage302 classifies the mechanism boundary. |

## Proof Gate

| gate | status | metric | value | interpretation |
| --- | --- | --- | --- | --- |
| G1_two_parameter_highstat | PASS | params | SET_2_3_2048;SET_4_5_2048 | Both tested parameters need 10-run/10-trial local complete-SAB evidence. |
| G2_counter_mechanism | PASS | cycles/loads | 1.045496632/1.038873490 | Native counters must support the memory/instruction mechanism direction. |
| G3_claim_boundary | PASS_SCOPED_ONLY | scope | two local binary include-zero 2048-output parameter sets | This is not universal parameter coverage or theoretical optimality. |
| G4_decision | PASS_STAGE304_TWO_PARAMETER_LOCAL_GENERALIZATION_WITH_COUNTER_MECHANISM | stage decision | PASS_STAGE304_TWO_PARAMETER_LOCAL_GENERALIZATION_WITH_COUNTER_MECHANISM | Controls Stage305 route. |
