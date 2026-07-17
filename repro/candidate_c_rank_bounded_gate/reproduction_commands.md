# Candidate C Rank-Bounded Gate Reproduction

Implementation-input commit: `a05e86113384a5c6cf6927d3f1e1127b43fe0366`

```text
python scripts/run_candidate_c_rank_bounded_gate.py --input-commit a05e86113384a5c6cf6927d3f1e1127b43fe0366
python scripts/apply_candidate_c_rank_bounded_gate.py --input-commit a05e86113384a5c6cf6927d3f1e1127b43fe0366
python scripts/build_mat_sab_selector_techgraph.py --input-commit a05e86113384a5c6cf6927d3f1e1127b43fe0366
python -m unittest discover -s tests/research -p "test_*.py" -v
python scripts/mat_sab_research_state.py validate
git diff --check
```
