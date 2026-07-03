# Stage198 Reproduction Commands

```powershell
# Rebuild the metadata-safe manuscript refresh
python scripts\build_stage198_metadata_safe_manuscript_refresh.py

# Inspect draft and compliance tables
Get-Content -Raw repro\stage198_metadata_safe_manuscript_refresh\manuscript_draft.md
Get-Content -Raw repro\stage198_metadata_safe_manuscript_refresh\paragraph_compliance.csv
Get-Content -Raw repro\stage198_metadata_safe_manuscript_refresh\claim_guard.csv

# Inspect upstream support bank
Get-Content -Raw repro\stage197_metadata_safe_citation_bank\sentence_support_bank.csv
```
