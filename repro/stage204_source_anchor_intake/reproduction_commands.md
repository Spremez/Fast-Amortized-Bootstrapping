# Stage204 Reproduction Commands

```powershell
python -m py_compile scripts\build_stage204_source_anchor_intake.py
python scripts\build_stage204_source_anchor_intake.py
Get-Content -Raw repro\stage204_source_anchor_intake\summary.csv
Get-Content -Raw repro\stage204_source_anchor_intake\proof_gate.csv
```

External source checks used during intake:

```powershell
Invoke-WebRequest https://raw.githubusercontent.com/antoniocgj/Fast-Amortized-Bootstrapping/main/README.md
Invoke-WebRequest https://askcryp.to/t/resource-topic-2025-686-fast-amortized-bootstrapping-with-small-keys-and-polynomial-noise-overhead/23992
Invoke-WebRequest https://antonioguimaraes.org/publication/guimaraes-fast-2025/
```
