# Stage260 Non-Binary Full SAB Noise/Resource

Decision: `PASS_STAGE260_NONBINARY_FULL_SAB_NOISE_RESOURCE`.

Stage260 records a small multi-trial full-path gate for the explicit
non-binary PVW/MAT-SAB path. It covers include-zero and ternary modes, r=1/2/4,
and trials=3. The primary endpoint is zero final PVW/scalar/pair failures; the
secondary endpoints are zero stage-pair failures and recorded non-binary
selector key-size/keygen estimates.

This is still not target-parameter performance evidence. The primary final
metric remains:

```text
T_bootstrap / r
```

## Final Noise

| mode | r | trials | points | pvw_failures | scalar_failures | pair_failures | pvw_log2_sigma_torus | scalar_log2_sigma_torus | pair_log2_sigma_torus | gate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| include_zero | 1 | 3 | 48 | 0 | 0 | 0 | -11.561 | -11.409 | -11.094 | PASS |
| include_zero | 2 | 3 | 96 | 0 | 0 | 0 | -11.441 | -11.556 | -10.954 | PASS |
| include_zero | 4 | 3 | 192 | 0 | 0 | 0 | -12.050 | -11.550 | -11.484 | PASS |
| ternary | 1 | 3 | 48 | 0 | 0 | 0 | -12.038 | -11.794 | -11.457 | PASS |
| ternary | 2 | 3 | 96 | 0 | 0 | 0 | -11.547 | -11.766 | -11.232 | PASS |
| ternary | 4 | 3 | 192 | 0 | 0 | 0 | -11.427 | -11.607 | -10.923 | PASS |

## Stage Pair Noise

| mode | stage | r | trials | points | pair_failures | pair_log2_sigma_torus | pair_log2_max_abs_torus |
| --- | --- | --- | --- | --- | --- | --- | --- |
| include_zero | blind_rotate_coeff0 | 1 | 3 | 48 | 0 | -12.945 | -12.306 |
| include_zero | extract | 1 | 3 | 48 | 0 | -12.945 | -12.306 |
| include_zero | materialize_tlwe | 1 | 3 | 48 | 0 | -12.945 | -12.306 |
| include_zero | packing_ks | 1 | 3 | 48 | 0 | -12.945 | -12.307 |
| include_zero | hw_ks | 1 | 3 | 48 | 0 | -11.283 | -9.922 |
| include_zero | blind_rotate_coeff0 | 2 | 3 | 96 | 0 | -13.112 | -12.500 |
| include_zero | extract | 2 | 3 | 96 | 0 | -13.112 | -12.500 |
| include_zero | materialize_tlwe | 2 | 3 | 96 | 0 | -13.112 | -12.500 |
| include_zero | packing_ks | 2 | 3 | 96 | 0 | -13.111 | -12.501 |
| include_zero | hw_ks | 2 | 3 | 96 | 0 | -11.627 | -10.198 |
| include_zero | blind_rotate_coeff0 | 4 | 3 | 192 | 0 | -13.072 | -12.275 |
| include_zero | extract | 4 | 3 | 192 | 0 | -13.072 | -12.275 |
| include_zero | materialize_tlwe | 4 | 3 | 192 | 0 | -13.072 | -12.275 |
| include_zero | packing_ks | 4 | 3 | 192 | 0 | -13.072 | -12.275 |
| include_zero | hw_ks | 4 | 3 | 192 | 0 | -11.634 | -9.651 |
| ternary | blind_rotate_coeff0 | 1 | 3 | 48 | 0 | -12.978 | -12.494 |
| ternary | extract | 1 | 3 | 48 | 0 | -12.978 | -12.494 |
| ternary | materialize_tlwe | 1 | 3 | 48 | 0 | -12.978 | -12.494 |
| ternary | packing_ks | 1 | 3 | 48 | 0 | -12.978 | -12.493 |
| ternary | hw_ks | 1 | 3 | 48 | 0 | -11.491 | -10.213 |
| ternary | blind_rotate_coeff0 | 2 | 3 | 96 | 0 | -13.032 | -12.348 |
| ternary | extract | 2 | 3 | 96 | 0 | -13.032 | -12.348 |
| ternary | materialize_tlwe | 2 | 3 | 96 | 0 | -13.032 | -12.348 |
| ternary | packing_ks | 2 | 3 | 96 | 0 | -13.032 | -12.348 |
| ternary | hw_ks | 2 | 3 | 96 | 0 | -11.481 | -10.143 |
| ternary | blind_rotate_coeff0 | 4 | 3 | 192 | 0 | -13.085 | -12.519 |
| ternary | extract | 4 | 3 | 192 | 0 | -13.085 | -12.519 |
| ternary | materialize_tlwe | 4 | 3 | 192 | 0 | -13.085 | -12.519 |
| ternary | packing_ks | 4 | 3 | 192 | 0 | -13.084 | -12.518 |
| ternary | hw_ks | 4 | 3 | 192 | 0 | -11.438 | -10.106 |

## Resources

| mode | r | pvw_estimated_key_bytes | scalar_repeated_estimated_key_bytes | pvw_vs_scalar_repeated_ratio | pvw_sab_keygen_us | scalar_repeated_sab_keygen_us |
| --- | --- | --- | --- | --- | --- | --- |
| include_zero | 1 | 1063104 | 1062880 | 1.000211 | 43183 | 44201 |
| include_zero | 2 | 2203520 | 2125760 | 1.036580 | 89962 | 78942 |
| include_zero | 4 | 5026608 | 4251520 | 1.182308 | 247262 | 162537 |
| ternary | 1 | 1063104 | 1062880 | 1.000211 | 35589 | 36505 |
| ternary | 2 | 2203520 | 2125760 | 1.036580 | 81998 | 74403 |
| ternary | 4 | 5026608 | 4251520 | 1.182308 | 219689 | 155879 |

## Source Matrix

| check | path | observed | gate | notes |
| --- | --- | --- | --- | --- |
| test_flag | src/mosfhet/Makefile.def | present | PASS | isolated Stage260 flag |
| test_harness | main.c | present | PASS | multi-trial full-path noise/resource harness |
| nonbinary_key_estimate_scalar | main.c | present | PASS | resource estimate includes extra scalar selector family |
| nonbinary_key_estimate_pvw | main.c | present | PASS | resource estimate includes extra MAT selector family |
| scalar_sab_unchanged | src/sparse_amortized_bootstrap.c | not_changed | PASS | scalar baseline remains the oracle |
| default_binary_build | repro/stage260_nonbinary_full_sab_noise_resource/build_ffnt_default_binary.log | compiled | PASS | default binary build still compiles |

## Admission

| route | decision | production_permission | reason | next_gate |
| --- | --- | --- | --- | --- |
| stage261_nonbinary_target_perf_t_bootstrap_per_bit | ADMIT_TARGET_PERF_PREFLIGHT | explicit_nonbinary_path_only | small full-path non-binary multi-trial noise/resource gate passes | same-backend complete SAB A/B with T_bootstrap/r |
| nonbinary_full_sab_speedup | BLOCKED | no | no target-parameter full SAB benchmark and no T_bootstrap/r result yet | Stage261 target performance |
| paper_claim | WAIT_STAGE261_AND_LITERATURE | no_novelty_claim | small FFNT correctness/resource evidence is not a paper-grade performance or novelty claim | target benchmark, statistics, and citation-safe related work |

## Claim Boundary

| claim | status | allowed_wording | forbidden_wording | evidence |
| --- | --- | --- | --- | --- |
| nonbinary_full_sab_small_noise_resource | supported_small_gate | The explicit non-binary PVW/MAT full SAB path passes a 3-trial small FFNT noise/resource gate for include-zero and ternary r=1/2/4. | The target 686 non-binary full SAB path has validated noise/resource behavior. | repro/stage260_nonbinary_full_sab_noise_resource/final_noise_summary.csv |
| stage_pair_equivalence | supported_small_gate | The recorded blind-rotate, extract, materialize, packing-KS, and HW-KS stage pair failures are zero for the small gate. | All target-parameter stages have zero failure probability. | repro/stage260_nonbinary_full_sab_noise_resource/stage_noise_summary.csv |
| full_sab_speedup | unsupported | Stage260 does not measure complete SAB speedup. | Stage260 proves bootstrapping acceleration. | repro/stage260_nonbinary_full_sab_noise_resource/implementation_admission.csv |
| amortized_time_per_plaintext_bit | unsupported_for_nonbinary | T_bootstrap/r remains the primary metric for Stage261+. | Non-binary T_bootstrap/r improved. | repro/stage260_nonbinary_full_sab_noise_resource/claim_boundary.csv |

## Proof Gate

| gate | status | metric | value | evidence | interpretation |
| --- | --- | --- | --- | --- | --- |
| G1_build | PASS | ffnt nonbinary full noise/resource build | compiled | repro/stage260_nonbinary_full_sab_noise_resource/build_ffnt_nonbinary_full_noise.log | Portable small full-path gate; no performance claim. |
| G2_final_noise | PASS | mode/r final rows | 6/6 | repro/stage260_nonbinary_full_sab_noise_resource/final_noise_summary.csv | Final output PVW/scalar/paired failures are zero for all small-gate rows. |
| G3_stage_noise | PASS | stage summary rows | 30/30 | repro/stage260_nonbinary_full_sab_noise_resource/stage_noise_summary.csv | All recorded intermediate pair-noise summaries have zero pair failures. |
| G4_resource | PASS | resource rows | 6/6 | repro/stage260_nonbinary_full_sab_noise_resource/resource_summary.csv | Small-gate key-size and keygen resource estimates are recorded. |
| G5_source_isolation | PASS | explicit path and scalar isolation | preserved | repro/stage260_nonbinary_full_sab_noise_resource/source_matrix.csv | Stage260 adds an explicit measurement flag; scalar SAB source is unchanged. |
| G6_stage261_admission | PASS_STAGED_ONLY | next route | ADMIT_TARGET_PERF_PREFLIGHT | repro/stage260_nonbinary_full_sab_noise_resource/implementation_admission.csv | Proceed to target performance preflight, but speedup remains blocked. |
| G7_stage260_decision | PASS_STAGE260_NONBINARY_FULL_SAB_NOISE_RESOURCE | decision | PASS_STAGE260_NONBINARY_FULL_SAB_NOISE_RESOURCE | repro/stage260_nonbinary_full_sab_noise_resource/proof_gate.csv | Small non-binary full-path noise/resource gate is complete. |

Generated from input head `cc6067f`.
