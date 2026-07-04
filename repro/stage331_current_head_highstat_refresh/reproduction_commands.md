# Stage331 Reproduction Commands

```sh
STAGE331_PERF_RUNS=10 STAGE331_NOISE_TRIALS=10 FFT_LIB=spqlios_avx512 PARAM=SET_2_3_2048 bash scripts/run_stage331_current_head_highstat_refresh.sh
```

Smoke:

```sh
STAGE331_PERF_RUNS=1 STAGE331_NOISE_TRIALS=1 FFT_LIB=spqlios_avx512 PARAM=SET_2_3_2048 bash scripts/run_stage331_current_head_highstat_refresh.sh
```
