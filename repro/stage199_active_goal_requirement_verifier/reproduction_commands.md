# Stage199 Reproduction Commands

```powershell
# Rebuild the active-goal verifier
python scripts\build_stage199_active_goal_requirement_verifier.py

# Inspect requirement and gap matrices
Get-Content -Raw repro\stage199_active_goal_requirement_verifier\requirement_matrix.csv
Get-Content -Raw repro\stage199_active_goal_requirement_verifier\evidence_gap_register.csv
Get-Content -Raw repro\stage199_active_goal_requirement_verifier\next_action_selector.csv

# Inspect current scoped writing and citation boundary
Get-Content -Raw repro\stage198_metadata_safe_manuscript_refresh\summary.csv
Get-Content -Raw repro\stage196_public_source_refresh\citation_gate.csv
```
