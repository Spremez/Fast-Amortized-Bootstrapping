# Stage230 Reproduction Commands

```powershell
python scripts\build_stage230_source_verified_literature_novelty_audit.py
Get-Content repro\stage230_source_verified_literature_novelty_audit\proof_gate.csv
Get-Content repro\stage230_source_verified_literature_novelty_audit\source_verification_refresh.csv
```

Manual source refresh queries are recorded in `search_queries.csv`. Use primary
or official metadata pages first: IACR ePrint, DOI pages, ACM/Springer/Dagstuhl,
USENIX, DBLP, and official project repositories.
