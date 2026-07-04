# Stage257 Experiment Plan

Executed smoke command:

```powershell
make clean
make FFT_LIB=ffnt SAB_PVW_NONBINARY_TEST=true KEY=BINARY PARAM=SET_2_3_2048 ARCH_FLAGS=
.\main
make clean
make FFT_LIB=ffnt KEY=BINARY PARAM=SET_2_3_2048 ARCH_FLAGS=
```

Evidence:

- `repro/stage257_nonbinary_sparsemul_implementation/build_ffnt_nonbinary_test.log`
- `repro/stage257_nonbinary_sparsemul_implementation/run_ffnt_nonbinary_test.log`
- `repro/stage257_nonbinary_sparsemul_implementation/proof_gate.csv`

Next experiment must move from staged lane equivalence to deterministic and
multi-seed sparse_mul correctness/noise, then full non-binary SAB A/B.
