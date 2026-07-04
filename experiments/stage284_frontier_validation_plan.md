# Stage284 Frontier Validation Plan

## Immediate Gates

| priority | route | entry_condition | gate | failure_action |
| --- | --- | --- | --- | --- |
| P0 | stage285_native_target_rerun | Stage283 native access missing | Rerun selected candidate and fast control on native target with T_bootstrap/r. | Keep all target performance and counter claims local/proxy only. |
| P1 | stage286_mat_ep_split_counter_gate | MAT EP remains largest selected-candidate profile share. | Split MAT EP into decompose/DFT/FMA/load-store attribution and require full SAB A/B before promotion. | Do not edit hot path; record as counter/proxy-only. |
| P2 | stage287_from_dft_lifecycle_design | from_DFT share remains high after selected candidate. | Alias-safe lifecycle design, isolated equivalence, then repeated T_bootstrap/r. | Reject if repeated full SAB is neutral. |
| P3 | stage288_body_linear_selector_proof | pursue theoretical optimum beyond exact dense format. | Distribution/security/noise proof for a new selector/key format before any hot-path code. | Keep dense exact path as scoped engineering route. |

## Required Statistics

- Use repeated complete-SAB `T_bootstrap/r`; do not use profiled runs for final
  latency claims.
- Record mean, min, max, and conservative guards at minimum.
- Keep native target evidence separate from WSL/proxy evidence.
- Treat Amdahl rows as planning evidence only.

## Reproduction

```bash
python3 scripts/build_stage284_frontier_gap_ledger.py
```
