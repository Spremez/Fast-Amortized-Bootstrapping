# Stage308 SPQLIOS IFFT Feasibility Audit

Decision: `PASS_STAGE308_IFFT_BACKEND_LOWLEVEL_REQUIRED_DIGIT_PATH_NEXT`.

Stage308 checks whether the Stage307 `ifft` residual has an existing low-risk SPQLIOS batching route. It does not change code paths or claim new speedup.

## Summary

| decision | stage307_digit_share | stage307_ifft_share | existing_batch_ifft_api | array_wrapper_is_per_row_loop | near_term_route | backend_route |
| --- | --- | --- | --- | --- | --- | --- |
| PASS_STAGE308_IFFT_BACKEND_LOWLEVEL_REQUIRED_DIGIT_PATH_NEXT | 0.481687 | 0.504577 | NO | YES | stage309_digit_to_double_avx512_candidate | stage310_spqlios_batched_ifft_design |

## Source Interface Audit

| source | evidence | status | location |
| --- | --- | --- | --- |
| src/mosfhet/src/fft/spqlios/spqlios-fft.h | ifft signature | SINGLE_BUFFER_API | src/mosfhet/src/fft/spqlios/spqlios-fft.h:24 |
| spqlios source set | batch ifft API search | ABSENT | regex ifft_(array\|batch\|many), batch_*ifft, ifft*rows |
| src/mosfhet/src/polynomial.c | polynomial_torus_to_DFT_array | PER_ROW_IFFT_LOOP | src/mosfhet/src/polynomial.c:435 |
| src/mosfhet/src/fft/spqlios/spqlios-ifft-avx512.s | assembly entry | SINGLE_DATA_POINTER_ENTRY | src/mosfhet/src/fft/spqlios/spqlios-ifft-avx512.s:18 |
| src/mosfhet/src/mattrgsw.c | digit-to-double AVX512 path | LOCAL_C_AVX512_CANDIDATE | src/mosfhet/src/mattrgsw.c:979 |

## Route Matrix

| route | priority | evidence | risk | gate |
| --- | --- | --- | --- | --- |
| stage309_digit_to_double_avx512_candidate | P0 | digit share 0.481687; local `_mm512_cvtepi64_pd` path | medium | profile flag shows lower digit_us; correctness passes; full SAB A/B required before promotion |
| stage310_spqlios_batched_ifft_design | P1 | ifft share 0.504577; no existing batch API | high | new API/model/assembly or C fallback, isolated FFT correctness, then complete-SAB A/B |
| dense_mat_avx512_rewrite | defer | Stage301/302 counters and Stage305/307 route do not select dense as the current residual target | medium | return only after DFT lifecycle stops dominating |

## Proof Gate

| gate | status | metric | value | interpretation |
| --- | --- | --- | --- | --- |
| G1_stage307_input | PASS | Stage307 decision | PASS_STAGE307_DIRECT_IFFT_LIFECYCLE_PROFILE_RECORDED | Stage308 must be grounded in the direct lifecycle split. |
| G2_no_existing_batch_ifft_api | PASS | source search | absent | No low-risk batch IFFT call can be wired directly. |
| G3_existing_wrappers_filtered | PASS | Stage289/290 | NEUTRAL_STAGE289_DFT_ARRAY_WRAPPER_NO_PROMOTION;NEUTRAL_STAGE290_DFT_DIRECT_OUTPUT_NO_PROMOTION | Previously tested DFT wrappers should not be repeated. |
| G4_digit_substantial | PASS | digit share | 0.481687 | A local digit materialization candidate is justified even though ifft is slightly larger. |
| G5_claim_boundary | PASS | scope | route audit | Stage308 is not a performance or novelty claim. |
| G6_decision | PASS_STAGE308_IFFT_BACKEND_LOWLEVEL_REQUIRED_DIGIT_PATH_NEXT | stage decision | PASS_STAGE308_IFFT_BACKEND_LOWLEVEL_REQUIRED_DIGIT_PATH_NEXT | Controls Stage309/310 split between local C optimization and backend FFT research. |
