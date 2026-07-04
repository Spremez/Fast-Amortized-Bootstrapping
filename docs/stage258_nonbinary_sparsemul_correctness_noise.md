# Stage258 Non-Binary Sparse_Mul Correctness/Noise

Decision: `PASS_STAGE258_NONBINARY_SPARSEMUL_CORRECTNESS_NOISE`.

Stage258 is a research-process gate, not an optimization claim. It checks the
Stage257 explicit non-binary PVW/MAT sparse_mul path under multiple deterministic
trial inputs and records pair-noise against scalar lane references.

## Algorithm Scope

The tested object is:

```text
PVW/MAT sparse_mul_nonbinary(mode, r)
```

with `mode in {include_zero, ternary}` and `r in {1, 2, 4}`. Each PVW
ciphertext is interpreted as one shared mask plus `r` body lanes. The invariant
is:

```text
phase(acc_pvw.body[q][i]) == phase(acc_scalar[q][i])
```

for every recorded lane `q`, coefficient `i`, sparse step, and trial. This is
still below full SAB because blind rotation integration, extraction, packing
key-switching, and the primary metric `T_bootstrap/r` are not exercised here.

## Runtime Summary

| mode | r | trials | points | pair_failures | pair_log2_sigma_torus | pair_log2_max_abs_torus | gate |
| --- | --- | --- | --- | --- | --- | --- | --- |
| include_zero | 1 | 3 | 49152 | 0 | -13.014 | -11.968 | PASS |
| include_zero | 2 | 3 | 98304 | 0 | -13.025 | -11.942 | PASS |
| include_zero | 4 | 3 | 196608 | 0 | -13.009 | -11.971 | PASS |
| ternary | 1 | 3 | 49152 | 0 | -13.276 | -12.057 | PASS |
| ternary | 2 | 3 | 98304 | 0 | -13.237 | -11.990 | PASS |
| ternary | 4 | 3 | 196608 | 0 | -13.270 | -11.991 | PASS |

## Lane Noise

| mode | r | lane | trials | points | pair_failures | pair_log2_sigma_torus | pair_log2_max_abs_torus |
| --- | --- | --- | --- | --- | --- | --- | --- |
| include_zero | 1 | 0 | 3 | 49152 | 0 | -13.014 | -11.968 |
| include_zero | 2 | 0 | 3 | 49152 | 0 | -13.024 | -11.953 |
| include_zero | 2 | 1 | 3 | 49152 | 0 | -13.026 | -11.942 |
| include_zero | 4 | 0 | 3 | 49152 | 0 | -13.010 | -11.984 |
| include_zero | 4 | 1 | 3 | 49152 | 0 | -13.011 | -11.989 |
| include_zero | 4 | 2 | 3 | 49152 | 0 | -13.009 | -11.973 |
| include_zero | 4 | 3 | 3 | 49152 | 0 | -13.008 | -11.971 |
| ternary | 1 | 0 | 3 | 49152 | 0 | -13.276 | -12.057 |
| ternary | 2 | 0 | 3 | 49152 | 0 | -13.238 | -11.990 |
| ternary | 2 | 1 | 3 | 49152 | 0 | -13.236 | -11.992 |
| ternary | 4 | 0 | 3 | 49152 | 0 | -13.271 | -12.006 |
| ternary | 4 | 1 | 3 | 49152 | 0 | -13.270 | -12.009 |
| ternary | 4 | 2 | 3 | 49152 | 0 | -13.268 | -11.991 |
| ternary | 4 | 3 | 3 | 49152 | 0 | -13.270 | -12.006 |

## Source Isolation

| check | path | observed | gate | notes |
| --- | --- | --- | --- | --- |
| noise_flag | src/mosfhet/Makefile.def | present | PASS | explicit correctness/noise smoke flag only |
| noise_harness | main.c | present | PASS | multi-trial sparse_mul lane/noise gate |
| pair_noise_all_coeffs | main.c | present | PASS | phase-pair noise measured over all coefficients and lanes |
| scalar_sab_unchanged | src/sparse_amortized_bootstrap.c | not_changed | PASS | scalar baseline remains the comparison reference |
| noise_build | repro/stage258_nonbinary_sparsemul_correctness_noise/build_ffnt_nonbinary_noise.log | compiled | PASS | portable FFNT correctness smoke, not performance |
| default_binary_build | repro/stage258_nonbinary_sparsemul_correctness_noise/build_ffnt_default_binary.log | compiled | PASS | default binary build still compiles |

## Admission

| route | decision | production_permission | reason | next_gate |
| --- | --- | --- | --- | --- |
| stage259_nonbinary_full_sab_integration_preflight | ADMIT_FULL_SAB_PREFLIGHT | explicit_nonbinary_path_only | sparse_mul include-zero/ternary r=1/2/4 multi-trial equivalence and pair-noise gate pass | wire non-binary path into blind_rotate/bootstrap and test full SAB T_bootstrap/r |
| nonbinary_full_sab_speedup | BLOCKED | no | no complete non-binary SAB route, no full extract/KS path, and no T_bootstrap/r benchmark yet | Stage259 full-SAB preflight then deterministic full-SAB correctness |
| default_binary_sab | NO_CHANGE | no_default_change | Stage258 adds a gated test harness only and default FFNT binary build passes | keep scalar/binary regression for every promoted change |

## Claim Boundary

| claim | status | allowed_wording | forbidden_wording | evidence |
| --- | --- | --- | --- | --- |
| nonbinary_sparsemul_correctness_noise | supported_staged | The explicit non-binary PVW/MAT sparse_mul path passes a 3-trial staged equivalence/noise gate for include-zero and ternary r=1/2/4. | The non-binary full SAB bootstrap is correct. | repro/stage258_nonbinary_sparsemul_correctness_noise/runtime_summary.csv |
| nonbinary_noise_vs_scalar_pair | supported_staged | PVW body lanes match scalar-lane references with zero pair failures over all recorded Stage258 sparse_mul coefficients. | Complete SAB failure rate is unchanged. | repro/stage258_nonbinary_sparsemul_correctness_noise/noise_lane.csv |
| full_sab_speedup | unsupported | Stage258 does not measure complete SAB speedup. | Stage258 proves bootstrapping acceleration. | repro/stage258_nonbinary_sparsemul_correctness_noise/implementation_admission.csv |
| amortized_time_per_plaintext_bit | unsupported_for_nonbinary | T_bootstrap/r remains the primary metric for Stage259+ complete-SAB evaluation. | Non-binary T_bootstrap/r improved. | repro/stage258_nonbinary_sparsemul_correctness_noise/claim_boundary.csv |

## Proof Gate

| gate | status | metric | value | evidence | interpretation |
| --- | --- | --- | --- | --- | --- |
| G1_build | PASS | ffnt nonbinary noise build | compiled | repro/stage258_nonbinary_sparsemul_correctness_noise/build_ffnt_nonbinary_noise.log | Portable correctness smoke only; no performance claim. |
| G2_runtime_summary | PASS | mode/r summary rows | 6/6 | repro/stage258_nonbinary_sparsemul_correctness_noise/runtime_summary.csv | include-zero and ternary r=1/2/4 pass with zero pair failures. |
| G3_lane_noise | PASS | lane rows | 14/14 | repro/stage258_nonbinary_sparsemul_correctness_noise/noise_lane.csv | All body lanes are checked against scalar-lane references over all coefficients. |
| G4_source_isolation | PASS | test harness and default isolation | preserved | repro/stage258_nonbinary_sparsemul_correctness_noise/source_matrix.csv | The scalar/default path remains isolated; Stage258 adds only gated measurement code. |
| G5_stage259_admission | PASS_STAGED_ONLY | next route | ADMIT_FULL_SAB_PREFLIGHT | repro/stage258_nonbinary_sparsemul_correctness_noise/implementation_admission.csv | Full-SAB integration may start, but speedup claims remain blocked. |
| G6_stage258_decision | PASS_STAGE258_NONBINARY_SPARSEMUL_CORRECTNESS_NOISE | decision | PASS_STAGE258_NONBINARY_SPARSEMUL_CORRECTNESS_NOISE | repro/stage258_nonbinary_sparsemul_correctness_noise/proof_gate.csv | Proceed to Stage259 full non-binary SAB integration preflight. |

Generated from input head `1d69fa5`.
