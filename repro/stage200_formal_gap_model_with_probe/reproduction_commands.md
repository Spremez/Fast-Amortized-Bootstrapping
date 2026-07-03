# Stage200 Reproduction Commands

```powershell
# Rebuild the formal gap model and finite probes
python scripts\build_stage200_formal_gap_model_with_probe.py

# Inspect the model and executable probes
Get-Content -Raw repro\stage200_formal_gap_model_with_probe\lower_bound_model.csv
Get-Content -Raw repro\stage200_formal_gap_model_with_probe\finite_probe.csv
Get-Content -Raw repro\stage200_formal_gap_model_with_probe\counterexample_matrix.csv
Get-Content -Raw repro\stage200_formal_gap_model_with_probe\summary.csv
```
