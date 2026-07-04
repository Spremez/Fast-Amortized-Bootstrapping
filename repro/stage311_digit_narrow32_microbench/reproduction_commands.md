# Stage311 Reproduction Commands

```bash
STAGE311_RUNS=5 STAGE311_REPS=5000 FFT_LIB=spqlios_avx512 \
  bash scripts/run_stage311_digit_narrow32_microbench.sh
python3 scripts/build_stage311_digit_narrow32_microbench.py
```
