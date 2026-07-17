# MAT-SAB Campaign Gaps

## Campaign State

- Goal: `ACTIVE`
- Paper gate: `BLOCKED`
- Candidate A: `REJECTED`
- Candidate B: `REJECTED`
- Candidate C: `INTAKE` (active)
- Last decision: `REJECT_CANDIDATE_B_EXACT_STANDARD_PVW_FACTORIZATION_ROUTE_TO_C`
- Disposition: Candidate B is closed after failing the exact standard-PVW factorization gate.

Candidate C is active at `INTAKE`; its equations and implementation have not begun.

Production code permission: `false`.

The closed Candidate A result is a finite-field necessary-condition rejection; it does not infer cryptographic security or complete-SAB performance.

## Open Obligations

- Candidate C rank-bounded shared-mask state equation gate (not begun)
- phase and rank-growth checks for the admitted accumulator state
- public relinearization cost and lane-phase preservation
- Amdahl projection against exact-dense complete SAB
- isolated kernel and complete-SAB evidence

## Reproduction

```powershell
python scripts/build_mat_sab_selector_techgraph.py
python -m unittest discover -s tests/research -p "test_*.py" -v
```
