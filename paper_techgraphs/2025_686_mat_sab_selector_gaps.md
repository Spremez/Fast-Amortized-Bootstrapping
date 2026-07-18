# MAT-SAB Campaign Gaps

## Campaign State

- Goal: `RESEARCH_CAMPAIGN_EXHAUSTED`
- Paper gate: `BLOCKED`
- Candidate A: `REJECTED`
- Candidate B: `REJECTED`
- Candidate C: `REJECTED` (active)
- Last decision: `REJECT_CANDIDATE_C_RANK_BOUNDED_STATE_CAMPAIGN_EXHAUSTED`
- Disposition: The finite A/B/C mechanism campaign is exhausted; Candidate C closed on its scoped C1 nonpositive structural-cost failure.

Task 3B and Task 4 were skipped; exact-dense PVW/MAT-SAB evidence is preserved; no Candidate D is opened automatically.

Production code permission: `false`.

The closed Candidate A result is a finite-field necessary-condition rejection; it does not infer cryptographic security or complete-SAB performance.

## Open Obligations

- Task 3B has no C2 seed or material; Task 4 is SKIPPED_NO_REGISTERED_OPERATOR with no numeric complete-cost or Amdahl values.
- The exact-dense PVW/MAT-SAB implementation and its scoped measured result remain preserved.
- No Candidate D is opened automatically; any continuation requires a separately approved research design.

## Reproduction

```powershell
python scripts/build_mat_sab_selector_techgraph.py --source-state-commit 9b4b461bc44c51db2b07f6c1e0eac0a063150dcb
python -m unittest discover -s tests/research -p "test_*.py" -v
```
