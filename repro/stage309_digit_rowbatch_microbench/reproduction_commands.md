# Stage309 Reproduction Commands

```bash
STAGE309_RUNS=5 STAGE309_REPS=5000 FFT_LIB=spqlios_avx512 \
  bash scripts/run_stage309_digit_rowbatch_microbench.sh
python3 scripts/build_stage309_digit_rowbatch_microbench.py
```
