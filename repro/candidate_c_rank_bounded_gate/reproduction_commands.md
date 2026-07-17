# Candidate C Rank-Bounded Gate Reproduction

Implementation-input commit: `6a3004cdf0fb5c35aeffe3984512657f8d2856ce`

```text
python scripts/run_candidate_c_rank_bounded_gate.py --input-commit 6a3004cdf0fb5c35aeffe3984512657f8d2856ce
python scripts/apply_candidate_c_rank_bounded_gate.py --input-commit 6a3004cdf0fb5c35aeffe3984512657f8d2856ce
python scripts/build_mat_sab_selector_techgraph.py --input-commit 6a3004cdf0fb5c35aeffe3984512657f8d2856ce
python -m unittest discover -s tests/research -p "test_*.py" -v
python scripts/mat_sab_research_state.py validate
git diff --check
```
