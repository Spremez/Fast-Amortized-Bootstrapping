# Stage310 Reproduction Commands

```bash
STAGE310_REPS=5000 FFT_LIB=spqlios_avx512 \
  bash scripts/run_stage310_ifft_rows_scaling_bench.sh
python3 scripts/build_stage310_ifft_rows_scaling_bench.py
```
