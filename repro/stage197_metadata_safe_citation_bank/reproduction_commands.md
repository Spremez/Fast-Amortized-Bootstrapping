# Stage197 Reproduction Commands

```powershell
# Rebuild the support bank
python scripts\build_stage197_metadata_safe_citation_bank.py

# Inspect sentence-level writing support
Get-Content -Raw repro\stage197_metadata_safe_citation_bank\sentence_support_bank.csv

# Inspect paragraph mapping
Get-Content -Raw repro\stage197_metadata_safe_citation_bank\paragraph_support_map.csv

# Inspect guard status
Get-Content -Raw repro\stage197_metadata_safe_citation_bank\claim_guard.csv

# Inspect upstream source boundary used by this stage
Get-Content -Raw repro\stage196_public_source_refresh\citation_gate.csv
```
