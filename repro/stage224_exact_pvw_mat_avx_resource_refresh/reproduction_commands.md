# Stage224 Reproduction Commands

```powershell
python scripts\build_stage224_exact_pvw_mat_avx_resource_refresh.py
Get-Content repro/stage224_exact_pvw_mat_avx_resource_refresh/proof_gate.csv
Get-Content repro/stage224_exact_pvw_mat_avx_resource_refresh/perf_comparison.csv
```

Optional controls:

```powershell
$env:STAGE224_PERF_RUNS='3'
$env:SAB_PVW_BENCH_REPS='1'
```
