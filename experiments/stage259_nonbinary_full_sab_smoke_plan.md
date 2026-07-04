# Stage259 Experiment Plan

Primary endpoint:

```text
full SAB scalar/PVW phase equivalence for include-zero and ternary, r=1/2/4
```

Executed commands:

```powershell
make clean
make FFT_LIB=ffnt SAB_PVW_NONBINARY_FULL_TEST=true KEY=BINARY PARAM=SET_2_3_2048 ARCH_FLAGS=
.\main
make clean
make FFT_LIB=ffnt KEY=BINARY PARAM=SET_2_3_2048 ARCH_FLAGS=
python scripts\build_stage259_nonbinary_full_sab_smoke.py
```

Evidence:

- `repro/stage259_nonbinary_full_sab_smoke/runtime_summary.csv`
- `repro/stage259_nonbinary_full_sab_smoke/source_matrix.csv`
- `repro/stage259_nonbinary_full_sab_smoke/proof_gate.csv`

Next endpoint:

```text
multi-seed full-path correctness/noise/resource, then target T_bootstrap/r A/B
```
