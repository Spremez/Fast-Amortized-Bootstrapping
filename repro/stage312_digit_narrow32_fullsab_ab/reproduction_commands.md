# Stage312 Reproduction Commands

```bash
STAGE312_RUNS=5 STAGE312_REPS=1 FFT_LIB=spqlios_avx512 PARAM=SET_2_3_2048 \
  bash scripts/run_stage312_digit_narrow32_fullsab_ab.sh
python3 scripts/build_stage312_digit_narrow32_fullsab_ab.py
```
