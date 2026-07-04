# mat_rlwe_sab_stage232_selected_subset: Selected current-head preflight

## Summary

- Parent algorithm: 2025/686 sparse amortized bootstrapping.
- Focused module: exact dense PVW/MAT-SAB complete bootstrapping path.
- Optimization target: complete-SAB `T_bootstrap/r`.
- Status labels: [experiment checked, preflight only], [statistical evidence insufficient].
- Main hypothesis: exact dense PVW/MAT-SAB amortizes shared-mask work across r
  body lanes and improves per-lane full bootstrapping throughput versus repeated
  scalar SAB.

## Mathematical Definition

The state is the existing exact dense MAT-RLWE/PVW state: one shared mask and r
body lanes. Stage232 does not change ciphertext equations or hot-path code; it
refreshes a selected current-head evidence point for `SET_2_3_4096`, r=4.

## Pseudocode

```text
Input: binary SAB instance, PARAM=SET_2_3_4096, r=4
Output: preflight evidence package
1. Build scalar and PVW/MAT paths with identical backend flags.
2. Run 3 complete-SAB A/B trials and require per-run correctness Pass.
3. Run 3 deterministic noise seeds and require zero PVW/scalar/pair failures.
4. Run PVW and scalar resource probes and record keygen/key-size/RSS.
5. Label result as selected-subset preflight, not final matrix promotion.
```

## Delta From Original Algorithm

| Original component | Variant component | Relationship | Evidence/status |
| --- | --- | --- | --- |
| r independent scalar SAB executions | one exact dense PVW/MAT-SAB execution with r body lanes | amortizes shared state and key flow | `repro/stage232_selected_subset_fullstat_resource/performance_stats.csv` |
| scalar resource accounting | PVW/MAT resource accounting beside scalar repeated | reports side cost | `repro/stage232_selected_subset_fullstat_resource/resource_comparison.csv` |
| single-run smoke | 3-run/3-seed selected preflight | increases evidence but not final stats | `repro/stage232_selected_subset_fullstat_resource/gate_matrix.csv` |

## Complexity Change

- Time: measured as complete-SAB `T_bootstrap/r`; Stage232 mean speedup is in
  `repro/stage232_selected_subset_fullstat_resource/performance_stats.csv`.
- Memory/key: recorded in `repro/stage232_selected_subset_fullstat_resource/resource_comparison.csv`.
- What must still be measured: 10-run/20-seed full added-parameter matrix before
  paper-table promotion.

## Potential Failure Reasons

- The selected subset may not generalize to r=2 or `SET_4_5_2048`.
- n=3 timing variance may understate or overstate the true effect.
- The exact dense MAT route does not prove theoretical optimality or compact
  selector feasibility.

## Required Experiments

- Full added-parameter matrix if used in the main claim.
- Non-binary and compact-route design gates before any broader claim.
