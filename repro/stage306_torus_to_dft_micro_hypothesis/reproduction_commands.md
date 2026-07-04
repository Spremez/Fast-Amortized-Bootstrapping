# Stage306 Reproduction Commands

```bash
STAGE306_RUNS=5 STAGE306_REPS=5000 FFT_LIB=spqlios_avx512 \
  bash scripts/run_stage306_torus_to_dft_micro_hypothesis.sh
python3 scripts/build_stage306_torus_to_dft_micro_hypothesis.py
```
