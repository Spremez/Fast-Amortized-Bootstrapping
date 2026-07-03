# Stage225 Reproduction Commands

```powershell
python scripts\build_stage225_exact_refresh_noise_resource_rerun.py
Get-Content repro/stage225_exact_refresh_noise_resource_rerun/proof_gate.csv
Get-Content repro/stage225_exact_refresh_noise_resource_rerun/noise_aggregate.csv
Get-Content repro/stage225_exact_refresh_noise_resource_rerun/resource_comparison.csv
```

Optional controls:

```powershell
$env:STAGE225_NOISE_SEED_COUNT='3'
$env:STAGE225_RESOURCE_RUNS='1'
```
