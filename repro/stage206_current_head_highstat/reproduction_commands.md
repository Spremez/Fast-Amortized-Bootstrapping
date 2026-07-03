# Stage206 Reproduction Commands

```powershell
wsl --cd /mnt/d/codexprograms/whFast-Amortized-Bootstrapping/Fast-Amortized-Bootstrapping bash scripts/run_stage206_current_head_highstat.sh
python scripts\build_stage206_current_head_highstat.py
Get-Content -Raw repro\stage206_current_head_highstat\performance_stats.csv
Get-Content -Raw repro\stage206_current_head_highstat\noise_stats.csv
```
