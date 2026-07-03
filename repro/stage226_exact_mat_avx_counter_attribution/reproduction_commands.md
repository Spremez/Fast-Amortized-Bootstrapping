# Stage226 Reproduction Commands

```powershell
$env:STAGE226_REMOTE_SECRET='<runtime-only>'
python scripts\build_stage226_exact_mat_avx_counter_attribution.py
Get-Content repro\stage226_exact_mat_avx_counter_attribution\proof_gate.csv
Get-Content repro\stage226_exact_mat_avx_counter_attribution\attribution_summary.csv
```
