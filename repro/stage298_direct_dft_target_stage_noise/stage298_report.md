# Stage298 Direct DFT Target Stage Noise

Decision: `PASS_STAGE298_DIRECT_DFT_TARGET_STAGE_NOISE_LOCAL`.

Stage298 adds target-size include-zero stage-wise noise evidence for the
direct-DFT PVW/MAT-SAB candidate. It is a correctness/noise side condition for
the Stage296 complete-SAB `T_bootstrap/r` speedup, not a new performance result.

## Stage Summary

| stage | trials | points | pair_failures | pair_log2_sigma_torus | pair_log2_max_abs_torus |
| --- | --- | --- | --- | --- | --- |
| blind_rotate_coeff0 | 3 | 24576 | 0 | -15.090 | -13.030 |
| extract | 3 | 24576 | 0 | -15.090 | -13.030 |
| materialize_tlwe | 3 | 24576 | 0 | -15.090 | -13.030 |
| packing_ks | 3 | 24576 | 0 | -15.089 | -13.014 |
| hw_ks | 3 | 24576 | 0 | -8.076 | -6.003 |

## Proof Gate

| gate | status | metric | value | interpretation |
| --- | --- | --- | --- | --- |
| G1_prior_stage296 | PASS | Stage296 decision | positive | Stage-wise noise is tied to high-stat direct-DFT throughput. |
| G2_prior_stage297 | PASS | Stage297 decision | positive | Stage-wise noise is interpreted with resource side conditions present. |
| G3_stage_coverage | PASS | stages | blind_rotate_coeff0,extract,hw_ks,materialize_tlwe,packing_ks | All blind/extract/materialize/packing/HW-KS boundaries must be present. |
| G4_pair_failures | PASS | summary pair failures | 0 | Every stage summary must have zero PVW/scalar decoded pair failures. |
| G5_trials | PASS | trials | 3 | Stage298 is a local 3-trial target stage-wise gate. |
| G6_mode_gate | PASS | program gate | Pass | The executable harness must report Pass. |
| G7_claim_boundary | PASS | scope | local target include-zero r=4 | This is not native counter attribution or parameter generalization. |
| G8_decision | PASS_STAGE298_DIRECT_DFT_TARGET_STAGE_NOISE_LOCAL | stage decision | PASS_STAGE298_DIRECT_DFT_TARGET_STAGE_NOISE_LOCAL | Controls Stage299 route. |

Minimum stage sigma: `-15.090`. Maximum stage absolute delta log2: `-6.003`.

Generated from input head `53cba80`.
