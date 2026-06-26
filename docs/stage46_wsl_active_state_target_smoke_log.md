# Stage 46 WSL Active-State Target Smoke Log

Date: 2026-06-26

## Goal

Refresh target-shape PVW/MAT-SAB correctness on the selected WSL/Linux
performance platform after the Stage 45 active-state refactor.

## Command

```text
make FFT_LIB=spqlios_avx512 MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true \
  SAB_PVW_ACTIVE_BUFFER_FUSION=true SAB_PVW_TARGET_TEST=true \
  KEY=BINARY PARAM=SET_2_3_2048 -j16
./main
```

## Result

| check | status | artifact |
|---|---|---|
| WSL `spqlios_avx512` target full bootstrap gate | PASS | `repro/stage46_wsl_active_state_target_smoke/run.log` |

Observed pass lines:

```text
SAB_PVW target full bootstrap binary lane equivalence r=2 h=39 r_prec=7: Pass
SAB_PVW target full bootstrap gate: Pass
```

This is a correctness/build smoke for the current code head. It is not a new
latency benchmark and does not upgrade the MAT-AVX512 theoretical
load/store-optimality claim.

## Decision

The Stage 45 active-state refactor remains compatible with the WSL/Linux
`spqlios_avx512` target full bootstrap gate under the promoted explicit path:

```text
MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true
SAB_PVW_ACTIVE_BUFFER_FUSION=true
```
