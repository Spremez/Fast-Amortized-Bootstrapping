# Stage290 Reproduction Commands

```bash
STAGE290_RUNS=3 STAGE290_REPS=5000 FFT_LIB=spqlios_avx512 \
  bash scripts/run_stage290_dft_direct_output_microbench.sh
python3 scripts/build_stage290_dft_direct_output_microbench.py
```
