# Candidate C Rank-Bounded Gate Reproduction

Implementation-input commit: `1907fce4c6435ed9f3e483dc3521895bf5351c34`

```text
python scripts/run_candidate_c_rank_bounded_gate.py --input-commit 1907fce4c6435ed9f3e483dc3521895bf5351c34
python scripts/apply_candidate_c_rank_bounded_gate.py --input-commit 1907fce4c6435ed9f3e483dc3521895bf5351c34
python scripts/build_mat_sab_selector_techgraph.py --input-commit 1907fce4c6435ed9f3e483dc3521895bf5351c34
python -m unittest discover -s tests/research -p "test_*.py" -v
python scripts/mat_sab_research_state.py validate
git diff --check
```
