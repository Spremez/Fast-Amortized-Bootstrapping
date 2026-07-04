# Stage296 Reproduction Commands

```bash
STAGE296_PERF_RUNS=10 STAGE296_NOISE_TRIALS=10 FFT_LIB=spqlios_avx512 PARAM=SET_2_3_2048 bash scripts/run_stage296_direct_dft_highstat.sh
python3 scripts/build_stage296_direct_dft_highstat.py
```

Primary endpoint: complete SAB `T_bootstrap/r`.
Side condition: target final-output PVW/scalar decoded pair failures.
