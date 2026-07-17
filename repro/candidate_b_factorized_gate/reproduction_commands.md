# Candidate B Reproduction Commands

```text
python scripts/run_candidate_b_factorized_gate.py
python -m unittest tests.research.test_factorized_selector_model -v
python -m unittest tests.research.test_candidate_b_gate -v
python -m unittest discover -s tests/research -p "test_*.py" -v
python scripts/mat_sab_research_state.py validate
```
