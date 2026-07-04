# Stage303 Reproduction Commands

```bash
STAGE303_PERF_RUNS=10 STAGE303_NOISE_TRIALS=10 FFT_LIB=spqlios_avx512 PARAM=SET_4_5_2048 bash scripts/run_stage303_param_matrix_highstat.sh
python3 scripts/build_stage303_param_matrix_highstat.py
```

Primary endpoint: complete SAB `T_bootstrap/r`.
Side condition: target final-output PVW/scalar decoded pair failures.
