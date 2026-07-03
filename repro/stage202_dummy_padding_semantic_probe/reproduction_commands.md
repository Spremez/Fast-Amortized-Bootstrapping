# Stage202 Reproduction Commands

```powershell
# Rebuild dummy padding semantic probe
python scripts\build_stage202_dummy_padding_semantic_probe.py

# Inspect outputs
Get-Content -Raw repro\stage202_dummy_padding_semantic_probe\summary.csv
Get-Content -Raw repro\stage202_dummy_padding_semantic_probe\semantic_probe.csv
Get-Content -Raw repro\stage202_dummy_padding_semantic_probe\resource_model.csv
Get-Content -Raw repro\stage202_dummy_padding_semantic_probe\proof_gate.csv
```
