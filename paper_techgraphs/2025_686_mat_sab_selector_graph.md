# 2025/686 MAT-SAB Selector And State Graph

## Campaign State

- Goal: `RESEARCH_CAMPAIGN_EXHAUSTED`
- Paper gate: `BLOCKED`
- Candidate A: `REJECTED`
- Candidate B: `REJECTED`
- Candidate C: `REJECTED` (active)
- Last decision: `REJECT_CANDIDATE_C_RANK_BOUNDED_STATE_CAMPAIGN_EXHAUSTED`
- Disposition: The finite A/B/C mechanism campaign is exhausted; Candidate C closed on its scoped C1 nonpositive structural-cost failure.

Task 3B and Task 4 were skipped; exact-dense PVW/MAT-SAB evidence is preserved; no Candidate D is opened automatically.

```mermaid
flowchart TD
  sab_schedule["sab_schedule: scalar SAB butterfly and sparse schedule"]
  pvw_phase["pvw_phase: phase map b_q - a*s_q"]
  pvw_randomization["pvw_randomization: shared random mask and r body corrections"]
  dense_keygen["dense_keygen: standard dense MAT-GGSW row sampling"]
  dense_decompose["dense_decompose: decompose all k+r components"]
  dense_addmul["dense_addmul: dense selector-output products"]
  compact_kernel["compact_kernel: lane-local compact evaluator"]
  generalized_lane_pair["generalized_lane_pair: closure-restoring but performance-negative lane-pair input"]
  shared_mask_kernel["shared_mask_kernel: positive isolated compact-kernel evidence"]
  closure_failure["closure_failure: compact output not closed as standard PVW state"]
  star_cycle_support["star_cycle_support: 4r declared active support"]
  neighbor_gap["neighbor_gap: lane-local API lacks neighbor-capable selector"]
  distribution_blocker["distribution_blocker: public compact-saving pattern remains distinguishable"]
  finite_semantic_zero["finite_semantic_zero: finite semantic-zero pass with security open"]
  sab_schedule -->|"each MAT CMUX invokes external-product decomposition"| dense_decompose
  dense_decompose -->|"m*T streams feed m*m*T products"| dense_addmul
  pvw_randomization -->|"every selector column is a PVW ciphertext sample"| dense_keygen
  pvw_phase -->|"output must preserve all r phase equations"| closure_failure
  shared_mask_kernel -->|"local speedup alone does not close the SAB state"| closure_failure
  generalized_lane_pair -->|"closure restoration repeats expensive transforms"| closure_failure
  star_cycle_support -->|"cycle terms require neighbor-capable output"| neighbor_gap
  star_cycle_support -->|"semantic sparsity must not become public leakage"| distribution_blocker
  finite_semantic_zero -->|"finite algebra is not a distribution proof"| distribution_blocker
```

## Anchors

| node | path | status |
| --- | --- | --- |
| sab_schedule | `src/sparse_amortized_bootstrap.c` | PASS |
| pvw_phase | `src/mosfhet/src/pvwtmlwe.c` | PASS |
| pvw_randomization | `src/mosfhet/src/pvwtmlwe.c` | PASS |
| dense_keygen | `src/mosfhet/src/mattrgsw.c` | PASS |
| dense_decompose | `src/mosfhet/src/mattrgsw.c` | PASS |
| dense_addmul | `src/mosfhet/src/mattrgsw.c` | PASS |
| compact_kernel | `src/mosfhet/src/mattrgsw.c` | PASS |
| generalized_lane_pair | `repro/stage134_generalized_lane_pair_input_ep_gate/summary.csv` | PASS |
| shared_mask_kernel | `repro/stage138_shared_mask_compact_gate/summary.csv` | PASS |
| closure_failure | `repro/stage139_compact_closure_audit/summary.csv` | PASS |
| star_cycle_support | `repro/stage203_production_selector_equation_probe/equation_map.csv` | PASS |
| neighbor_gap | `repro/stage222_isolated_compact_ep_integration/expressiveness_results.csv` | PASS |
| distribution_blocker | `repro/stage249_structured_compact_distribution_security/claim_boundary.csv` | PASS |
| finite_semantic_zero | `repro/stage329_formal_compact_selector_checker/summary.csv` | PASS |

## Reproduction

```powershell
python scripts/build_mat_sab_selector_techgraph.py --input-commit 61b511feb39a261e3a404ee8108d7e6d05a5b1de
python -m unittest discover -s tests/research -p "test_*.py" -v
```
