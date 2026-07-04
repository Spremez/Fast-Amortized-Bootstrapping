# Stage257 Non-Binary Sparse_Mul Implementation

Decision: `PASS_STAGE257_NONBINARY_SPARSEMUL_IMPLEMENTED_STAGED`.

Stage257 is the first production-code checkpoint for the non-binary
PVW/MAT-SAB route. It adds explicit `sab_pvw_*` APIs for include-zero and
ternary sparse_mul, but it does not claim complete bootstrapping speedup.

## Implemented Algorithm

For each sparse secret step, the distance-bit RGSW monomial schedule is reused:

```text
p <- RGSW_monomial_mul_state(p, s_distance[step])
```

The branch-specific update is then:

```text
include-zero: p[j] <- p[j] + EP(s_coff[step], (X^a[j] - 1) p[j])
ternary:      p[j] <- X^a[j] p[j] + EP(s_sign[step], (X^(-2a[j]) - 1) X^a[j] p[j])
```

The final distance-bit RGSW step is unchanged. The PVW ciphertext still has one
shared mask and `r` body lanes; this gate checks r=1/2/4.

## API Matrix

| api | declared | defined | notes |
| --- | --- | --- | --- |
| sab_pvw_new_nonbinary_key | yes | yes | explicit non-binary PVW sparse_mul path only |
| sab_pvw_sub_a_include_zero | yes | yes | explicit non-binary PVW sparse_mul path only |
| sab_pvw_sub_a_ternary | yes | yes | explicit non-binary PVW sparse_mul path only |
| sab_pvw_sparse_mul_nonbinary | yes | yes | explicit non-binary PVW sparse_mul path only |

## Runtime Equivalence

| mode | r | h | r_prec | status | evidence |
| --- | --- | --- | --- | --- | --- |
| include_zero | 1 | 2 | 3 | PASS | repro/stage257_nonbinary_sparsemul_implementation/run_ffnt_nonbinary_test.log |
| include_zero | 2 | 2 | 3 | PASS | repro/stage257_nonbinary_sparsemul_implementation/run_ffnt_nonbinary_test.log |
| include_zero | 4 | 2 | 3 | PASS | repro/stage257_nonbinary_sparsemul_implementation/run_ffnt_nonbinary_test.log |
| ternary | 1 | 2 | 3 | PASS | repro/stage257_nonbinary_sparsemul_implementation/run_ffnt_nonbinary_test.log |
| ternary | 2 | 2 | 3 | PASS | repro/stage257_nonbinary_sparsemul_implementation/run_ffnt_nonbinary_test.log |
| ternary | 4 | 2 | 3 | PASS | repro/stage257_nonbinary_sparsemul_implementation/run_ffnt_nonbinary_test.log |

## Source Isolation

| file | change | observed | gate |
| --- | --- | --- | --- |
| include/sab_pvw.h | optional s_coff/s_sign fields and explicit non-binary API declarations | changed | PASS |
| src/sab_pvw.c | explicit non-binary keygen, sub_a, and sparse_mul implementation | changed | PASS |
| src/sparse_amortized_bootstrap.c | scalar SAB reference remains untouched | not_changed | PASS |
| src/sab_pvw.c | binary blind rotate continues to call sab_pvw_sparse_mul_binary | yes | PASS |
| Makefile/src | default binary FFNT build still compiles | compiled | PASS |

## Admission

| route | decision | production_permission | reason | next_gate |
| --- | --- | --- | --- | --- |
| stage258_nonbinary_sparsemul_correctness_noise | ADMIT_STAGED_CORRECTNESS_NOISE | explicit_nonbinary_path_only | r=1/2/4 include-zero and ternary sparse_mul lane equivalence pass | deterministic and multi-seed sparse_mul correctness/noise before full SAB |
| default_binary_sab | NO_CHANGE | no_default_change | binary blind rotate and bootstrap path still call sab_pvw_sparse_mul_binary | binary regression build/run after each promoted change |
| nonbinary_full_sab_speedup | BLOCKED | no | no non-binary blind_rotate/bootstrap/full extract integration or T_bootstrap/r benchmark yet | Stage258+Stage259 |

## Claim Boundary

| claim | status | allowed_wording | forbidden_wording | evidence |
| --- | --- | --- | --- | --- |
| nonbinary_sparsemul_implementation | supported_staged | An explicit non-binary PVW/MAT sparse_mul path is implemented and passes staged lane equivalence for include-zero and ternary r=1/2/4. | Full non-binary PVW/MAT-SAB bootstrapping is complete. | repro/stage257_nonbinary_sparsemul_implementation/runtime_equivalence.csv |
| full_sab_speedup | unsupported | No non-binary complete-SAB speedup is claimed at Stage257. | Stage257 accelerates complete SAB bootstrapping. | repro/stage257_nonbinary_sparsemul_implementation/implementation_admission.csv |
| amortized_time_per_plaintext_bit | unsupported_for_nonbinary | T_bootstrap/r remains the final metric for complete-SAB evaluation. | Non-binary T_bootstrap/r improved. | repro/stage257_nonbinary_sparsemul_implementation/claim_boundary.csv |

## Proof Gate

| gate | status | metric | value | evidence | interpretation |
| --- | --- | --- | --- | --- | --- |
| G1_build | PASS | ffnt build | compiled | repro/stage257_nonbinary_sparsemul_implementation/build_ffnt_nonbinary_test.log | Portable build smoke gate only, not performance evidence. |
| G2_api_surface | PASS | declared;defined | all | repro/stage257_nonbinary_sparsemul_implementation/api_matrix.csv | Explicit non-binary API is present without replacing binary API. |
| G3_runtime_equivalence | PASS | mode/r pass rows | 6/6 | repro/stage257_nonbinary_sparsemul_implementation/runtime_equivalence.csv | include-zero and ternary sparse_mul staged lane equivalence pass for r=1/2/4. |
| G4_source_isolation | PASS | default path isolation | preserved | repro/stage257_nonbinary_sparsemul_implementation/source_change_matrix.csv | Scalar SAB and binary PVW default route remain reference paths. |
| G5_admission | PASS_STAGED_ONLY | next route | explicit_nonbinary_path_only | repro/stage257_nonbinary_sparsemul_implementation/implementation_admission.csv | Next work is correctness/noise, not full-SAB speedup claim. |
| G6_stage257_decision | PASS_STAGE257_NONBINARY_SPARSEMUL_IMPLEMENTED_STAGED | decision | PASS_STAGE257_NONBINARY_SPARSEMUL_IMPLEMENTED_STAGED | repro/stage257_nonbinary_sparsemul_implementation/proof_gate.csv | Proceed to Stage258 sparse_mul correctness/noise and then full SAB integration. |

Generated from input head `c919276`.
