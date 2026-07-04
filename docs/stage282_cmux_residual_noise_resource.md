# Stage282 CMUX Residual Noise/Resource Gate

Decision: `PASS_STAGE282_NOISE_RESOURCE_LOCAL_PASS_NATIVE_REQUIRED`.

Stage282 checks the selected `backend_sub_decomp_dual` candidate against the
guarded fast control on the existing include-zero full-smoke noise/resource
harness. This run uses `ffnt` as a correctness/resource proxy because the
small full-smoke harness is not stable under `spqlios_avx512`; it is not
target-parameter AVX512 latency evidence.

| variant | status | trials | pvw failures | scalar failures | pair failures | key ratio | max RSS KB |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| fast_control | pass | 3 | 0 | 0 | 0 | 1.182308 | 20476 |
| backend_sub_decomp_dual | pass | 3 | 0 | 0 | 0 | 1.182308 | 20348 |

## Proof Gate

| gate | status | metric | value | interpretation |
| --- | --- | --- | --- | --- |
| G1_input | PASS | input commit | 6646ba0 | Stage282 starts after Stage281 repeated positive gate. |
| G2_noise_resource | PASS | variant pass count | 2/2 | Both fast control and selected candidate must pass. |
| G3_failures | PASS | failures | 0 required | No PVW/scalar/pair failures accepted. |
| G4_resource_reporting | PASS | key/RSS rows | present | Resource costs are reported, not hidden. |
| G5_decision | PASS_STAGE282_NOISE_RESOURCE_LOCAL_PASS_NATIVE_REQUIRED | stage decision | PASS_STAGE282_NOISE_RESOURCE_LOCAL_PASS_NATIVE_REQUIRED | Native target-parameter confirmation remains separate. |

Generated from input head `6646ba0`.
