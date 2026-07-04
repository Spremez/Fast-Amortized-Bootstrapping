# Stage294 Reproduction Commands

```bash
STAGE294_TRIALS=3 FFT_LIB=spqlios_avx512 PARAM=SET_2_3_2048 bash scripts/run_stage294_direct_dft_target_noise.sh
python3 scripts/build_stage294_direct_dft_target_noise.py
```

Primary evidence: target-size include-zero final-output noise for the direct
DFT PVW/MAT-SAB candidate.
