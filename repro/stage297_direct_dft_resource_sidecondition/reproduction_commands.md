# Stage297 Reproduction Commands

```bash
STAGE297_TRIALS=1 FFT_LIB=spqlios_avx512 PARAM=SET_2_3_2048 bash scripts/run_stage297_direct_dft_resource_sidecondition.sh
python3 scripts/build_stage297_direct_dft_resource_sidecondition.py
```

This stage records a target final-output RSS/correctness probe for
selected-control and direct-DFT. It links key/keygen/RSS fields from Stage293
and high-stat throughput from Stage296.
