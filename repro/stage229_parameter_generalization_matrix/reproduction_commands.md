# Stage229 Reproduction Commands

```powershell
python scripts\build_stage229_parameter_generalization_matrix.py
Get-Content repro\stage229_parameter_generalization_matrix\proof_gate.csv
Get-Content repro\stage229_parameter_generalization_matrix\parameter_matrix.csv
Get-Content repro\stage229_parameter_generalization_matrix\coverage_gaps.csv
```

Optional current-head smoke probe, not a parameter-generalization claim:

```powershell
bash -lc "make clean >/dev/null 2>&1 || true && make FFT_LIB=spqlios_avx512 A_PRNG=none ENABLE_VAES=false PARAM=SET_2_3 KEY=BINARY MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true MAT_TRGSW_AVX512_RGT4_FUSED=true SAB_PVW_ACTIVE_BUFFER_FUSION=true SAB_PVW_BACKEND_FROM_DFT_ADD=true SAB_PVW_BENCH=true SAB_PVW_BENCH_R=2 SAB_PVW_BENCH_REPS=1 -j2 && ./main"
```

The optional probe must be interpreted from printed `h`, `r_prec`, and `in_N`.
If it prints the default target shape, it is only a smoke probe.
