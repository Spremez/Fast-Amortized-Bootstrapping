# Stage123 Production FFT Smoke Model

Date: 2026-07-03

Stage123 is the first vector-shared structured EP gate that links against
the production MOSFHET polynomial and SPQLIOS DFT API. It still uses a
standalone smoke probe, not SAB hot-path integration. The smoke compares
three phases:

1. dense message-reference phase from active shared/body messages;
2. coefficient-domain structured EP phase using MOSFHET torus
   polynomial multiplication;
3. production DFT-domain structured EP phase using
   `polynomial_torus_to_DFT`, `polynomial_mul_addto_DFT`, and
   `polynomial_DFT_to_torus`.

DFT comparisons use a fixed 1024 torus-unit tolerance because
production SPQLIOS uses floating-point transforms. This is smoke
evidence, not a noise proof.

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

| r | N | dense terms | structured terms | ratio | scope |
|---:|---:|---:|---:|---:|---|
| 2 | 1024 | 6 | 4 | 1.500000 | production_fft_smoke |
| 4 | 1024 | 20 | 8 | 2.500000 | production_fft_smoke |
| 6 | 1024 | 42 | 12 | 3.500000 | production_fft_smoke |
| 2 | 2048 | 6 | 4 | 1.500000 | production_fft_smoke |

## Boundary

This gate does not define new MOSFHET ciphertext structs, key generation,
gadget decomposition, extraction, key switching, AVX512 optimality, SAB
schedule integration, or complete `T_bootstrap/r` acceleration.
