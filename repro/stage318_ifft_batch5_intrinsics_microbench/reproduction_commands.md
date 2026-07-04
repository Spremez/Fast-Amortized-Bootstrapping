# Stage318 Reproduction Commands

```sh
make FFT_LIB=spqlios_avx512 MAT_TRGSW_IFFT_BATCH5_BENCH=true MAT_TRGSW_IFFT_BATCH5_BENCH_REPS=5000
./main
objdump -d -Mintel --disassemble=ifft_batch5_tile32 build/spqlios-fft-impl-avx512.o
```

Official Stage318 timing evidence uses WSL/Linux.  Windows MinGW AVX512 builds
are treated as unsupported proxy evidence for this stage.
