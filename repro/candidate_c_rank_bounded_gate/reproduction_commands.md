# Candidate C Rank-Bounded Gate Reproduction

Implementation-input commit: `cca8c7127575767448d5caf99a2b66f4299e8332`

```text
python scripts/run_candidate_c_rank_bounded_gate.py --input-commit cca8c7127575767448d5caf99a2b66f4299e8332
python scripts/apply_candidate_c_rank_bounded_gate.py --input-commit cca8c7127575767448d5caf99a2b66f4299e8332
python -m unittest discover -s tests/research -p "test_*.py" -v
python scripts/mat_sab_research_state.py validate
git diff --check
```
