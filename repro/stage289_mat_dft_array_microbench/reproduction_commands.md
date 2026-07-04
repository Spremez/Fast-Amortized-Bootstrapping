# Stage289 Reproduction Commands

```bash
STAGE289_RUNS=3 STAGE289_REPS=5000 FFT_LIB=spqlios_avx512 \
  bash scripts/run_stage289_mat_dft_array_microbench.sh
python3 scripts/build_stage289_mat_dft_array_microbench.py
```
