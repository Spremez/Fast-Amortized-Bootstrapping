# Stage123 Production FFT Smoke Gate

Date: 2026-07-03

## Decision

`PASS_STAGE123_PRODUCTION_FFT_SMOKE_READY_MOSFHET_TYPE_SKETCH_REQUIRED`

Stage123 links a standalone structured EP smoke probe against the actual
MOSFHET static library built with `FFT_LIB=spqlios`. It remains outside
`sab_pvw_*` and does not change scalar/default behavior.

## Gates

| gate | status | metric | value | detail |
|---|---|---|---|---|
| stage123_mosfhet_static_build | PASS | make_static_spqlios | true | MOSFHET static library build using FFT_LIB=spqlios. |
| stage123_probe_compile | PASS | gcc_probe_compile | true | Standalone structured EP smoke probe linked against libmosfhet.a. |
| stage123_probe_run | PASS | probe_returncode | 0 | Production FFT smoke probe executed. |
| stage123_coeff_reference | PASS | coeff_expected_mismatches | 0;0;0;0;0;0;0 | Coefficient-domain structured EP phase matches dense message-reference phase exactly. |
| stage123_production_fft_boundary | PASS_WITH_TOLERANCE | dft_coeff_mismatches;max_gap;tolerance | 0;0;0;0;0;0;0;619;1024 | Production SPQLIOS DFT multiply-add structured EP matches coefficient EP within tolerance. |
| stage123_noisy_fft_boundary | PASS_WITH_TOLERANCE | noisy_dft_coeff_mismatches;max_gap;tolerance | 0;0;0;0;0;0;0;619;1024 | Noisy structured EP also crosses production FFT within tolerance. |
| stage123_negative_control | PASS_REJECTS_BODY_ONLY_SKIP | negative_control_failures | 2048;2048;4096;4096;6144;6144;4096 | Body-only off-lane skip remains rejected under the production smoke model. |
| stage123_layout_terms | PASS | min_ep_term_ratio | 1.500000 | Smoke scope preserves Stage122 structured term ratios. |
| stage123_decision | PASS_STAGE123_PRODUCTION_FFT_SMOKE_READY_MOSFHET_TYPE_SKETCH_REQUIRED | next_gate_policy |  | Production FFT smoke passes outside `sab_pvw_*`. |

## Smoke Rows

| backend | r | N | seed | coeff mismatches | DFT mismatches | noisy DFT mismatches | negative failures | max DFT gap | tolerance | status |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| spqlios | 2 | 1024 | 0 | 0 | 0 | 0 | 2048 | 267 | 1024 | PASS_PRODUCTION_FFT_SMOKE |
| spqlios | 2 | 1024 | 1 | 0 | 0 | 0 | 2048 | 246 | 1024 | PASS_PRODUCTION_FFT_SMOKE |
| spqlios | 4 | 1024 | 0 | 0 | 0 | 0 | 4096 | 267 | 1024 | PASS_PRODUCTION_FFT_SMOKE |
| spqlios | 4 | 1024 | 1 | 0 | 0 | 0 | 4096 | 246 | 1024 | PASS_PRODUCTION_FFT_SMOKE |
| spqlios | 6 | 1024 | 0 | 0 | 0 | 0 | 6144 | 267 | 1024 | PASS_PRODUCTION_FFT_SMOKE |
| spqlios | 6 | 1024 | 1 | 0 | 0 | 0 | 6144 | 303 | 1024 | PASS_PRODUCTION_FFT_SMOKE |
| spqlios | 2 | 2048 | 0 | 0 | 0 | 0 | 4096 | 619 | 1024 | PASS_PRODUCTION_FFT_SMOKE |

## Layout Rows

| r | N | dense EP | structured EP | ratio | status |
|---:|---:|---:|---:|---:|---|
| 2 | 1024 | 6 | 4 | 1.500000 | PASS_LAYOUT |
| 4 | 1024 | 20 | 8 | 2.500000 | PASS_LAYOUT |
| 6 | 1024 | 42 | 12 | 3.500000 | PASS_LAYOUT |
| 2 | 2048 | 6 | 4 | 1.500000 | PASS_LAYOUT |

## Interpretation

This removes the production FFT smoke blocker for small structured EP
instances. It still does not prove a new MOSFHET type, real selector/key
generation, gadget decomposition, AVX512 optimality, SAB schedule
integration, or complete-SAB speedup.
