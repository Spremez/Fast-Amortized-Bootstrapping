# Candidate C Rank-Bounded Gate Reproduction

Implementation-input commit: `d0095120442e4a1dfdb9c1410bddae9ce74a9bf9`

```text
python scripts/run_candidate_c_rank_bounded_gate.py --input-commit d0095120442e4a1dfdb9c1410bddae9ce74a9bf9
python scripts/apply_candidate_c_rank_bounded_gate.py --input-commit d0095120442e4a1dfdb9c1410bddae9ce74a9bf9
python -m unittest discover -s tests/research -p "test_*.py" -v
python scripts/mat_sab_research_state.py validate
git diff --check
```
