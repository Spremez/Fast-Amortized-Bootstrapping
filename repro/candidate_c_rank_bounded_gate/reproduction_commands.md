# Candidate C Rank-Bounded Gate Reproduction

Implementation-input commit: `61b511feb39a261e3a404ee8108d7e6d05a5b1de`

```text
python scripts/run_candidate_c_rank_bounded_gate.py --input-commit 61b511feb39a261e3a404ee8108d7e6d05a5b1de
python scripts/apply_candidate_c_rank_bounded_gate.py --input-commit 61b511feb39a261e3a404ee8108d7e6d05a5b1de
python scripts/build_mat_sab_selector_techgraph.py --input-commit 61b511feb39a261e3a404ee8108d7e6d05a5b1de
python -m unittest discover -s tests/research -p "test_*.py" -v
python scripts/mat_sab_research_state.py validate
git diff --check
```
