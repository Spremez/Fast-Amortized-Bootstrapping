# Stage258 Reproduction Commands

```powershell
make clean
make FFT_LIB=ffnt SAB_PVW_NONBINARY_NOISE_TEST=true SAB_PVW_NONBINARY_NOISE_TRIALS=3 KEY=BINARY PARAM=SET_2_3_2048 ARCH_FLAGS=
.\main
make clean
make FFT_LIB=ffnt KEY=BINARY PARAM=SET_2_3_2048 ARCH_FLAGS=
python scripts\build_stage258_nonbinary_sparsemul_correctness_noise.py
```

The FFNT run is a correctness/noise smoke gate, not a performance benchmark.
Complete SAB acceleration must be measured later as `T_bootstrap/r`.
