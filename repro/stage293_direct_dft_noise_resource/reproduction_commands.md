# Stage293 Reproduction Commands

```bash
FFT_LIB=spqlios_avx512 PARAM=SET_2_3_2048 bash scripts/run_stage293_direct_dft_noise_resource.sh
python3 scripts/build_stage293_direct_dft_noise_resource.py
```

This stage records target correctness and target resource smoke for the direct
DFT candidate. It does not claim high-stat noise closure.
