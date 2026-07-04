# Stage299 Reproduction Commands

```bash
STAGE299_RUNS=3 STAGE299_NOISE_TRIALS=3 PARAM=SET_4_5_2048 FFT_LIB=spqlios_avx512 bash scripts/run_stage299_direct_dft_param_preflight.sh
python3 scripts/build_stage299_direct_dft_param_preflight.py
```

Primary endpoint: complete SAB `T_bootstrap/r`; side condition: final-output
PVW/scalar pair failures.
