# Stage342 Continuity Audit

Decision: `PASS_STAGE342_CONTINUITY_AUDIT_SCOPED_BRIDGE_NO_FULL_MATRIX_CLAIM`.

The current safe bridge is:

- current-head r=4 high-stat remains the primary scoped claim;
- current-head r=2 has a real smoke only;
- Stage36 target and added-parameter rows remain historical/supporting where
  hot-path changes prevent direct current-head promotion;
- full current-head parameter matrix is still incomplete.

| decision | primary_current_head_r4_speedup | r2_current_head_status | r2_smoke_speedup | full_matrix_status |
| --- | --- | --- | --- | --- |
| PASS_STAGE342_CONTINUITY_AUDIT_SCOPED_BRIDGE_NO_FULL_MATRIX_CLAIM | 1.747647 | smoke_only | 1.695000 | missing_current_head_highstat_cases |
