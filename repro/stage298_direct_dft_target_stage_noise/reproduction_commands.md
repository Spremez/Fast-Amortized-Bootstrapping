# Stage298 Reproduction Commands

```bash
STAGE298_TRIALS=3 FFT_LIB=spqlios_avx512 PARAM=SET_2_3_2048 bash scripts/run_stage298_direct_dft_target_stage_noise.sh
python3 scripts/build_stage298_direct_dft_target_stage_noise.py
```

Primary endpoint: zero PVW/scalar decoded pair failures at every target
stage boundary for direct-DFT include-zero r=4.
