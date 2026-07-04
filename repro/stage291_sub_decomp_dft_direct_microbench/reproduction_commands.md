# Stage291 Reproduction Commands

```bash
STAGE291_RUNS=5 STAGE291_REPS=5000 FFT_LIB=spqlios_avx512 \
  bash scripts/run_stage291_sub_decomp_dft_direct_microbench.sh
python3 scripts/build_stage291_sub_decomp_dft_direct_microbench.py
```
