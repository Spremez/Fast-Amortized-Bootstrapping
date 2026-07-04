# Stage294 Direct DFT Target Final-Output Noise

Decision: `PASS_STAGE294_DIRECT_DFT_TARGET_NOISE_FINAL_OUTPUT`.

Stage294 adds a target-size nonbinary/include-zero final-output noise harness
for the Stage292 direct-DFT candidate. This avoids the old `N=16` SPQLIOS
full-noise fixture and checks the actual `SET_2_3_2048`, r=4 path.

## Summary

| variant | mode | r | trials | points | expected_model_pvw_failures | expected_model_scalar_failures | pair_failures | pair_log2_sigma_torus | gate | overall_gate | decision |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| direct_dft_target_noise | include_zero | 4 | 3 | 24576 | 9216 | 9216 | 0 | -7.358 | Pass | Pass | PASS_STAGE294_DIRECT_DFT_TARGET_NOISE_FINAL_OUTPUT |

## Lanes

| lane | trials | expected_model_pvw_failures | expected_model_scalar_failures | pair_failures | expected_model_pvw_log2_sigma_torus | expected_model_scalar_log2_sigma_torus | pair_log2_sigma_torus |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | 3 | 2304 | 2304 | 0 | -2.215 | -2.212 | -7.500 |
| 1 | 3 | 2304 | 2304 | 0 | -2.215 | -2.212 | -7.680 |
| 2 | 3 | 2304 | 2304 | 0 | -2.215 | -2.212 | -7.520 |
| 3 | 3 | 2304 | 2304 | 0 | -2.215 | -2.215 | -6.957 |

## Proof Gate

| gate | status | metric | value | interpretation |
| --- | --- | --- | --- | --- |
| G1_stage292_full_sab | PASS | Stage292 full-SAB T/r | positive | Noise gate follows a full-SAB positive candidate. |
| G2_stage293_resource | PASS | Stage293 target correctness/resource | pass | Target correctness/resource smoke must precede stronger noise evidence. |
| G3_pair_failures | PASS | PVW/scalar decoded pair failures | 0 | Direct DFT output must decode identically to repeated scalar SAB. |
| G4_expected_model_boundary | INFO | expected-model mismatches | pvw=9216;scalar=9216 | The hand-written LUT model is diagnostic only for nonbinary packing; scalar reference equivalence is the gate. |
| G5_claim_boundary | PASS | scope | target final-output noise | This is not stage-wise noise, all-parameter noise, or paper-grade high-stat closure. |
| G6_decision | PASS_STAGE294_DIRECT_DFT_TARGET_NOISE_FINAL_OUTPUT | stage decision | PASS_STAGE294_DIRECT_DFT_TARGET_NOISE_FINAL_OUTPUT | Pass supports high-stat refresh and stage-wise repair next. |

Generated from input head `972c5b2`.
