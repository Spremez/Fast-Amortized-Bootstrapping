# Stage295 Reproduction Commands

```bash
STAGE295_PERF_RUNS=5 STAGE295_NOISE_TRIALS=5 FFT_LIB=spqlios_avx512 PARAM=SET_2_3_2048 bash scripts/run_stage295_direct_dft_stats_refresh.sh
python3 scripts/build_stage295_direct_dft_stats_refresh.py
```

Primary performance metric: complete SAB `T_bootstrap/r`.
Primary noise metric: target final-output PVW/scalar decoded pair failures.
