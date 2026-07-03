# Stage201 Reproduction Commands

```powershell
# Rebuild structured selector distribution probe
python scripts\build_stage201_structured_selector_distribution_probe.py

# Inspect outputs
Get-Content -Raw repro\stage201_structured_selector_distribution_probe\summary.csv
Get-Content -Raw repro\stage201_structured_selector_distribution_probe\distribution_probe.csv
Get-Content -Raw repro\stage201_structured_selector_distribution_probe\candidate_matrix.csv
Get-Content -Raw repro\stage201_structured_selector_distribution_probe\proof_gate.csv
```
