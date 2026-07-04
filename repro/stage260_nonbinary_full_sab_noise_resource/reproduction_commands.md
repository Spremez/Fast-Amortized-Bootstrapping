# Stage260 Reproduction Commands

```powershell
make clean
make FFT_LIB=ffnt SAB_PVW_NONBINARY_FULL_NOISE_TEST=true SAB_PVW_NONBINARY_FULL_NOISE_TRIALS=3 KEY=BINARY PARAM=SET_2_3_2048 ARCH_FLAGS=
.\main
make clean
make FFT_LIB=ffnt KEY=BINARY PARAM=SET_2_3_2048 ARCH_FLAGS=
python scripts\build_stage260_nonbinary_full_sab_noise_resource.py
```

This is a small FFNT full-path correctness/noise/resource gate. It is not a
target-parameter performance benchmark.
