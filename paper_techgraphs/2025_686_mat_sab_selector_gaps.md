# MAT-SAB Campaign Gaps

## Campaign State

- Goal: `ACTIVE`
- Paper gate: `BLOCKED`
- Candidate A: `REJECTED`
- Candidate B: `INTAKE` (active)
- Last decision: `REJECT_CANDIDATE_A_STANDARD_PVW_RANDOMIZATION_ROUTE_TO_B`
- Disposition: Candidate A is closed after failing the standard-PVW randomization necessary condition.

Candidate B is active at `INTAKE`; its equations and implementation have not begun.

Production code permission: `false`.

The closed Candidate A result is a finite-field necessary-condition rejection; it does not infer cryptographic security or complete-SAB performance.

## Open Obligations

- Candidate B factorized-operator equation gate (not begun)
- production key distribution and assumption comparison for an admitted representation
- noise recurrence under an admitted selector representation
- Amdahl projection against exact-dense complete SAB
- isolated kernel and complete-SAB evidence

## Reproduction

```powershell
python scripts/build_mat_sab_selector_techgraph.py
python -m unittest discover -s tests/research -p "test_*.py" -v
```
