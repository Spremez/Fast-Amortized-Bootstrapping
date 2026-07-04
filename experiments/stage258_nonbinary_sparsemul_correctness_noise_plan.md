# Stage258 Experiment Plan

Primary endpoint:

```text
zero pair failures for include-zero and ternary sparse_mul, r=1/2/4, trials=3
```

Executed commands:

```powershell
make clean
make FFT_LIB=ffnt SAB_PVW_NONBINARY_NOISE_TEST=true SAB_PVW_NONBINARY_NOISE_TRIALS=3 KEY=BINARY PARAM=SET_2_3_2048 ARCH_FLAGS=
.\main
make clean
make FFT_LIB=ffnt KEY=BINARY PARAM=SET_2_3_2048 ARCH_FLAGS=
python scripts\build_stage258_nonbinary_sparsemul_correctness_noise.py
```

Evidence:

- `repro/stage258_nonbinary_sparsemul_correctness_noise/runtime_summary.csv`
- `repro/stage258_nonbinary_sparsemul_correctness_noise/noise_lane.csv`
- `repro/stage258_nonbinary_sparsemul_correctness_noise/proof_gate.csv`

Next endpoint:

```text
full non-binary SAB correctness and T_bootstrap/r benchmark
```

No performance claim is made from FFNT or sparse_mul-only evidence.
