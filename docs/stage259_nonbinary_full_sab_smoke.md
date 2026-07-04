# Stage259 Non-Binary Full SAB Smoke

Decision: `PASS_STAGE259_NONBINARY_FULL_SAB_SMOKE`.

Stage259 adds an explicit non-binary PVW/MAT full SAB path and checks it against
scalar SAB on a small FFNT full-pipeline smoke. The exercised pipeline is:

```text
setup_tv_xb -> blind_rotate_nonbinary -> sparse_mul_nonbinary
  -> extract -> packing KS -> HW KS
```

The tested modes are include-zero and ternary, with r=1/2/4 body lanes. This is
the first full-pipeline non-binary correctness evidence, but it is not a target
parameter, multi-seed, noise, resource, or performance gate.

## Runtime Summary

| mode | r | h | r_prec | status | scope |
| --- | --- | --- | --- | --- | --- |
| include_zero | 1 | 2 | 3 | PASS | small_full_pipeline_ffnt_smoke |
| include_zero | 2 | 2 | 3 | PASS | small_full_pipeline_ffnt_smoke |
| include_zero | 4 | 2 | 3 | PASS | small_full_pipeline_ffnt_smoke |
| ternary | 1 | 2 | 3 | PASS | small_full_pipeline_ffnt_smoke |
| ternary | 2 | 2 | 3 | PASS | small_full_pipeline_ffnt_smoke |
| ternary | 4 | 2 | 3 | PASS | small_full_pipeline_ffnt_smoke |

## Source Matrix

| check | path | observed | gate | notes |
| --- | --- | --- | --- | --- |
| api_decl_new_nonbinary_full_key | include/sab_pvw.h | present | PASS | explicit full-key constructor declaration |
| api_decl_bootstrap_nonbinary | include/sab_pvw.h | present | PASS | explicit non-binary full bootstrap declaration |
| api_def_new_nonbinary_full_key | src/sab_pvw.c | present | PASS | constructor reuses non-binary keygen plus full postproc |
| api_def_blind_rotate_nonbinary | src/sab_pvw.c | present | PASS | blind rotate calls sparse_mul_nonbinary |
| api_def_bootstrap_nonbinary | src/sab_pvw.c | present | PASS | full path uses non-binary wo_extract and existing postproc |
| test_flag | src/mosfhet/Makefile.def | present | PASS | isolated FFNT smoke flag |
| test_harness | main.c | present | PASS | small full-pipeline scalar/PVW equivalence test |
| scalar_sab_unchanged | src/sparse_amortized_bootstrap.c | not_changed | PASS | scalar baseline remains the oracle |
| default_binary_build | repro/stage259_nonbinary_full_sab_smoke/build_ffnt_default_binary.log | compiled | PASS | default binary build still compiles |

## Admission

| route | decision | production_permission | reason | next_gate |
| --- | --- | --- | --- | --- |
| stage260_nonbinary_full_sab_noise_resource | ADMIT_NOISE_RESOURCE | explicit_nonbinary_path_only | small full-pipeline non-binary PVW/MAT SAB smoke passes for include-zero and ternary r=1/2/4 | multi-seed correctness/noise/resource for the non-binary full path |
| stage261_nonbinary_target_perf_t_bootstrap_per_bit | WAIT_STAGE260 | no_speedup_claim | target parameter performance requires noise/resource gate first | same-backend complete SAB A/B using T_bootstrap/r |
| nonbinary_full_sab_speedup | BLOCKED | no | no target-parameter benchmark, no multi-seed failure-rate gate, and no T_bootstrap/r result yet | Stage260 then Stage261 |

## Claim Boundary

| claim | status | allowed_wording | forbidden_wording | evidence |
| --- | --- | --- | --- | --- |
| nonbinary_full_sab_small_correctness | supported_smoke | The explicit non-binary PVW/MAT full SAB path passes small-parameter FFNT full-pipeline equivalence for include-zero and ternary r=1/2/4. | The target 686 non-binary full SAB path is fully validated. | repro/stage259_nonbinary_full_sab_smoke/runtime_summary.csv |
| default_scalar_baseline | preserved_build_gate | The scalar SAB source remains unchanged and the default binary FFNT build compiles. | Scalar SAB performance is unchanged. | repro/stage259_nonbinary_full_sab_smoke/source_matrix.csv |
| full_sab_speedup | unsupported | Stage259 does not measure complete SAB speedup. | Stage259 proves bootstrapping acceleration. | repro/stage259_nonbinary_full_sab_smoke/implementation_admission.csv |
| amortized_time_per_plaintext_bit | unsupported_for_nonbinary | T_bootstrap/r remains the primary metric for Stage261+. | Non-binary T_bootstrap/r improved. | repro/stage259_nonbinary_full_sab_smoke/claim_boundary.csv |

## Proof Gate

| gate | status | metric | value | evidence | interpretation |
| --- | --- | --- | --- | --- | --- |
| G1_build | PASS | ffnt nonbinary full build | compiled | repro/stage259_nonbinary_full_sab_smoke/build_ffnt_nonbinary_full.log | Portable full-pipeline smoke build; no performance claim. |
| G2_runtime_full_pipeline | PASS | mode/r pass rows | 6/6 | repro/stage259_nonbinary_full_sab_smoke/runtime_summary.csv | include-zero and ternary r=1/2/4 full-SAB smoke outputs match scalar references. |
| G3_source_isolation | PASS | explicit path and scalar isolation | preserved | repro/stage259_nonbinary_full_sab_smoke/source_matrix.csv | New code is an explicit non-binary path; scalar SAB source is unchanged. |
| G4_stage260_admission | PASS_STAGED_ONLY | next route | ADMIT_NOISE_RESOURCE | repro/stage259_nonbinary_full_sab_smoke/implementation_admission.csv | Proceed to multi-seed noise/resource, not performance claims. |
| G5_stage259_decision | PASS_STAGE259_NONBINARY_FULL_SAB_SMOKE | decision | PASS_STAGE259_NONBINARY_FULL_SAB_SMOKE | repro/stage259_nonbinary_full_sab_smoke/proof_gate.csv | Full non-binary path exists and passes small deterministic smoke. |

Generated from input head `16a18c1`.
