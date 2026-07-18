# Candidate C Rank-Bounded Gate Reproduction

Implementation-input commit: `d47f2db2f85362125d96bb584d658d7466028662`

```text
python scripts/run_candidate_c_rank_bounded_gate.py --input-commit d47f2db2f85362125d96bb584d658d7466028662
python scripts/apply_candidate_c_rank_bounded_gate.py --input-commit d47f2db2f85362125d96bb584d658d7466028662
python -m unittest discover -s tests/research -p "test_*.py" -v
python scripts/mat_sab_research_state.py validate
git diff --check
```
