# Stage122 Structured EP Arithmetic Gate

Date: 2026-07-03

## Decision

`PASS_STAGE122_STRUCTURED_EP_ARITHMETIC_READY_PRODUCTION_FFT_SMOKE_REQUIRED`

Stage122 checks vector-shared structured external-product arithmetic
against a dense clean phase reference and an exact DFT-domain
implementation. It remains outside `sab_pvw_*` and outside production
MOSFHET FFT/AVX512 code.

## Gates

| gate | status | metric | value | detail |
|---|---|---|---|---|
| stage122_compile | PASS | gcc_compile | true | Generated structured EP arithmetic C probe compiled under WSL gcc. |
| stage122_dense_vs_structured_phase | PASS | dense_structured_phase_mismatches | 0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0 | Structured vector-shared clean EP phase matches dense clean reference. |
| stage122_coeff_vs_dft_ep | PASS | structured_coeff_dft_mismatches | 0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0 | Structured coefficient-domain EP matches exact DFT-domain EP. |
| stage122_noisy_bound | PASS_BOUNDED | structured_noisy_bound_violations | 0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0 | Structured noisy EP remains within the conservative digit/noise bound. |
| stage122_negative_control | PASS_REJECTS_BODY_ONLY_SKIP | negative_control_failures | 64;62;63;64;60;127;126;127;123;128;126;127;122;126;127;254;254;249;256;256;191;191;189;188;189;380;384;380;381;383 | Body-only off-lane skip fails as expected, preserving the Stage112 warning. |
| stage122_layout_terms | PASS | min_ep_term_ratio;min_selector_poly_ratio | 1.500000;1.125000 | Structured EP keeps the term-count and selector-polynomial advantages in the prototype. |
| stage122_decision | PASS_STAGE122_STRUCTURED_EP_ARITHMETIC_READY_PRODUCTION_FFT_SMOKE_REQUIRED | next_gate_policy |  | Structured EP arithmetic passes outside SAB. |

## Layout Rows

| r | N | dense EP | structured EP | EP ratio | dense selector | structured selector | selector ratio | status |
|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 2 | 32 | 6 | 4 | 1.500000 | 9 | 8 | 1.125000 | PASS_LAYOUT |
| 2 | 64 | 6 | 4 | 1.500000 | 9 | 8 | 1.125000 | PASS_LAYOUT |
| 4 | 32 | 20 | 8 | 2.500000 | 25 | 16 | 1.562500 | PASS_LAYOUT |
| 4 | 64 | 20 | 8 | 2.500000 | 25 | 16 | 1.562500 | PASS_LAYOUT |
| 6 | 32 | 42 | 12 | 3.500000 | 49 | 24 | 2.041667 | PASS_LAYOUT |
| 6 | 64 | 42 | 12 | 3.500000 | 49 | 24 | 2.041667 | PASS_LAYOUT |

## Arithmetic Rows

| r | N | seed | dense/structured | coeff/DFT | noise violations | negative failures | EP ratio | status |
|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 2 | 32 | 0 | 0 | 0 | 0 | 64 | 1.500000 | PASS_STRUCTURED_EP_ARITHMETIC |
| 2 | 32 | 1 | 0 | 0 | 0 | 62 | 1.500000 | PASS_STRUCTURED_EP_ARITHMETIC |
| 2 | 32 | 2 | 0 | 0 | 0 | 63 | 1.500000 | PASS_STRUCTURED_EP_ARITHMETIC |
| 2 | 32 | 3 | 0 | 0 | 0 | 64 | 1.500000 | PASS_STRUCTURED_EP_ARITHMETIC |
| 2 | 32 | 4 | 0 | 0 | 0 | 60 | 1.500000 | PASS_STRUCTURED_EP_ARITHMETIC |
| 2 | 64 | 0 | 0 | 0 | 0 | 127 | 1.500000 | PASS_STRUCTURED_EP_ARITHMETIC |
| 2 | 64 | 1 | 0 | 0 | 0 | 126 | 1.500000 | PASS_STRUCTURED_EP_ARITHMETIC |
| 2 | 64 | 2 | 0 | 0 | 0 | 127 | 1.500000 | PASS_STRUCTURED_EP_ARITHMETIC |
| 2 | 64 | 3 | 0 | 0 | 0 | 123 | 1.500000 | PASS_STRUCTURED_EP_ARITHMETIC |
| 2 | 64 | 4 | 0 | 0 | 0 | 128 | 1.500000 | PASS_STRUCTURED_EP_ARITHMETIC |
| 4 | 32 | 0 | 0 | 0 | 0 | 126 | 2.500000 | PASS_STRUCTURED_EP_ARITHMETIC |
| 4 | 32 | 1 | 0 | 0 | 0 | 127 | 2.500000 | PASS_STRUCTURED_EP_ARITHMETIC |
| 4 | 32 | 2 | 0 | 0 | 0 | 122 | 2.500000 | PASS_STRUCTURED_EP_ARITHMETIC |
| 4 | 32 | 3 | 0 | 0 | 0 | 126 | 2.500000 | PASS_STRUCTURED_EP_ARITHMETIC |
| 4 | 32 | 4 | 0 | 0 | 0 | 127 | 2.500000 | PASS_STRUCTURED_EP_ARITHMETIC |
| 4 | 64 | 0 | 0 | 0 | 0 | 254 | 2.500000 | PASS_STRUCTURED_EP_ARITHMETIC |
| 4 | 64 | 1 | 0 | 0 | 0 | 254 | 2.500000 | PASS_STRUCTURED_EP_ARITHMETIC |
| 4 | 64 | 2 | 0 | 0 | 0 | 249 | 2.500000 | PASS_STRUCTURED_EP_ARITHMETIC |
| 4 | 64 | 3 | 0 | 0 | 0 | 256 | 2.500000 | PASS_STRUCTURED_EP_ARITHMETIC |
| 4 | 64 | 4 | 0 | 0 | 0 | 256 | 2.500000 | PASS_STRUCTURED_EP_ARITHMETIC |
| 6 | 32 | 0 | 0 | 0 | 0 | 191 | 3.500000 | PASS_STRUCTURED_EP_ARITHMETIC |
| 6 | 32 | 1 | 0 | 0 | 0 | 191 | 3.500000 | PASS_STRUCTURED_EP_ARITHMETIC |
| 6 | 32 | 2 | 0 | 0 | 0 | 189 | 3.500000 | PASS_STRUCTURED_EP_ARITHMETIC |
| 6 | 32 | 3 | 0 | 0 | 0 | 188 | 3.500000 | PASS_STRUCTURED_EP_ARITHMETIC |
| 6 | 32 | 4 | 0 | 0 | 0 | 189 | 3.500000 | PASS_STRUCTURED_EP_ARITHMETIC |
| 6 | 64 | 0 | 0 | 0 | 0 | 380 | 3.500000 | PASS_STRUCTURED_EP_ARITHMETIC |
| 6 | 64 | 1 | 0 | 0 | 0 | 384 | 3.500000 | PASS_STRUCTURED_EP_ARITHMETIC |
| 6 | 64 | 2 | 0 | 0 | 0 | 380 | 3.500000 | PASS_STRUCTURED_EP_ARITHMETIC |
| 6 | 64 | 3 | 0 | 0 | 0 | 381 | 3.500000 | PASS_STRUCTURED_EP_ARITHMETIC |
| 6 | 64 | 4 | 0 | 0 | 0 | 383 | 3.500000 | PASS_STRUCTURED_EP_ARITHMETIC |

## Interpretation

This removes the next finite arithmetic blocker: structured vector-shared
EP matches dense clean-reference phase and exact DFT EP matches
coefficient EP. It still does not prove production FFT behavior, gadget
decomposition, SAB schedule integration, or complete-SAB speedup.
