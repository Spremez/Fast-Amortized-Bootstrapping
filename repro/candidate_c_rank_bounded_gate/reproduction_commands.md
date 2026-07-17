# Candidate C Rank-Bounded Gate Reproduction

Implementation-input commit: `801a7833dc4b12cd57fc920030b837a348ffcc16`

```text
python scripts/run_candidate_c_rank_bounded_gate.py --input-commit 801a7833dc4b12cd57fc920030b837a348ffcc16
python scripts/apply_candidate_c_rank_bounded_gate.py --input-commit 801a7833dc4b12cd57fc920030b837a348ffcc16
python scripts/build_mat_sab_selector_techgraph.py --input-commit 801a7833dc4b12cd57fc920030b837a348ffcc16
python -m unittest discover -s tests/research -p "test_*.py" -v
python scripts/mat_sab_research_state.py validate
git diff --check
```
