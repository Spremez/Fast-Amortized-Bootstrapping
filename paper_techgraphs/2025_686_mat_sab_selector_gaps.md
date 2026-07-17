# Candidate A Pre-Production Gaps

Production code permission: `false`.

- standard PVW randomization dimension
- production key distribution and assumption comparison
- noise recurrence under the admitted selector representation
- Amdahl projection against exact-dense complete SAB
- isolated kernel and complete-SAB evidence

The next gate tests `P M = mu P` and the standard PVW randomization
dimension. It does not infer cryptographic security from finite arithmetic.

## Reproduction

```powershell
python scripts/build_mat_sab_selector_techgraph.py
python -m unittest discover -s tests/research -p "test_*.py" -v
```
