# Stage292 Reproduction Commands

```bash
STAGE292_RUNS=3 STAGE292_REPS=1 FFT_LIB=spqlios_avx512 PARAM=SET_2_3_2048 bash scripts/run_stage292_fullsab_direct_dft_ab.sh
python3 scripts/build_stage292_fullsab_direct_dft_ab.py
```

Primary endpoint: complete SAB `T_bootstrap/r` for r-body MAT-RLWE/PVW output.
