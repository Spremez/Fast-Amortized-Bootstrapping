# Stage319 Reproduction Commands

```sh
make FFT_LIB=spqlios_avx512 MAT_TRGSW_IFFT_BATCH5_ASM_BENCH=true MAT_TRGSW_IFFT_BATCH5_BENCH_REPS=5000
./main
objdump -d -Mintel --disassemble=ifft_batch5_tile32_asm build/spqlios-ifft-avx512.o
```
