# Candidate C Rank-Bounded Gate Reproduction

Implementation-input commit: `b9289d5b2adae07568888961743848ccb06b3571`

```text
python scripts/run_candidate_c_rank_bounded_gate.py --input-commit b9289d5b2adae07568888961743848ccb06b3571
python scripts/apply_candidate_c_rank_bounded_gate.py --input-commit b9289d5b2adae07568888961743848ccb06b3571
python -m unittest discover -s tests/research -p "test_*.py" -v
python scripts/mat_sab_research_state.py validate
git diff --check
```
