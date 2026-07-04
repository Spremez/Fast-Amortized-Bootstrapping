# Stage237 Reproduction Commands

Stage237 is an aggregation/report stage. It does not rerun SAB timings.

```bash
python scripts/build_stage237_scoped_manuscript_package.py
```

Primary input evidence:

```text
repro/stage236_set_2_3_4096_r4_highstat_slice/selected_binary_matrix_summary.csv
repro/stage230_source_verified_literature_novelty_audit/source_verification_refresh.csv
repro/stage230_source_verified_literature_novelty_audit/novelty_risk_map.csv
repro/stage227_exact_route_claim_boundary_update/claim_matrix.csv
```
