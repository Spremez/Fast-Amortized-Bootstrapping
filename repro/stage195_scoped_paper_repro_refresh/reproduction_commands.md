# Stage195 Reproduction Commands

This file records entry points for the current scoped report package.

```powershell
# Rebuild this package
python scripts\build_stage195_scoped_paper_repro_refresh.py

# Inspect primary result
Get-Content -Raw repro\stage178_fullmat_perbit_frontier\per_bit_throughput.csv

# Inspect compact admission blockers
Get-Content -Raw repro\stage192_compact_admission_route_selection\gate_admission_matrix.csv

# Inspect local implementation frontiers
Get-Content -Raw repro\stage193_exact_addmul_dataflow_preflight\summary.csv
Get-Content -Raw repro\stage194_exact_dft_conversion_preflight\summary.csv

# Validate generated claim guard
Get-Content -Raw repro\stage195_scoped_paper_repro_refresh\forbidden_claim_scan.csv
```
