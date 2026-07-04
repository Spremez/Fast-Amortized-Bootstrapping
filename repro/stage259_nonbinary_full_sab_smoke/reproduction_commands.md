# Stage259 Reproduction Commands

```powershell
make clean
make FFT_LIB=ffnt SAB_PVW_NONBINARY_FULL_TEST=true KEY=BINARY PARAM=SET_2_3_2048 ARCH_FLAGS=
.\main
make clean
make FFT_LIB=ffnt KEY=BINARY PARAM=SET_2_3_2048 ARCH_FLAGS=
python scripts\build_stage259_nonbinary_full_sab_smoke.py
```

This is a full-pipeline correctness smoke. It is not a target-parameter
performance benchmark.
