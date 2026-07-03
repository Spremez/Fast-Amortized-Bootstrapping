# Stage203 Reproduction Commands

```powershell
# Rebuild production-shaped selector equation probe
python scripts\build_stage203_production_selector_equation_probe.py

# Inspect outputs
Get-Content -Raw repro\stage203_production_selector_equation_probe\summary.csv
Get-Content -Raw repro\stage203_production_selector_equation_probe\equation_map.csv
Get-Content -Raw repro\stage203_production_selector_equation_probe\phase_noise_probe.csv
Get-Content -Raw repro\stage203_production_selector_equation_probe\proof_gate.csv
```
