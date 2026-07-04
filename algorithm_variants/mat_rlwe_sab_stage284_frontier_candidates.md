# Stage284 MAT-RLWE SAB Frontier Candidates

## Scope

This file records candidates admitted by the current frontier ledger.  Every
candidate must preserve scalar/default SAB behavior and must be evaluated using
complete-SAB `T_bootstrap/r`.

| candidate_id | algorithm_delta | measured_basis | theory_basis | risk | next_gate | status |
| --- | --- | --- | --- | --- | --- | --- |
| S284-A-current-selected-exact | Keep current exact dense backend_sub_decomp_dual path. | Stage281 repeated T_bootstrap/r plus Stage282 local noise/resource. | Same SAB schedule and same MAT selector/key semantics. | Native target and hardware-counter evidence missing. | Rerun Stage283 on authenticated native target. | local_positive_pending_native |
| S284-B-mat-ep-split-avx | Reduce MAT EP/sub-decomposition cost without changing selector semantics. | Current candidate MAT EP profile share 0.604066. | A same-format improvement can move T_bootstrap/r only if MAT EP reduction survives full SAB. | Native counters may show memory/FMA/register pressure not matching the source model. | Native counter plus split microbench, then full SAB A/B. | admitted_but_no_hot_path_edit_without_counter_or_split_gate |
| S284-C-from-dft-lifecycle | Shorten from_DFT/materialization lifetime around CMUX output. | Current candidate from_DFT profile share 0.358366. | Materialization traffic is large after backend direct-add and sub-decomp fusion. | Previous direct-add-only route was neutral; repeated full SAB gate is mandatory. | New alias-safe lifecycle design before implementation. | conditional_new_mechanism_required |
| S284-D-body-linear-selector-format | Change selector/key format toward body-linear or compact terms. | Stage166 r=4 dense/compact term ratio 1.923077. | Would attack the dense (r+1)^2 term risk instead of tuning one dense kernel. | Current compact/body-linear proxies are not admissible as exact dense lower bounds. | Separate distribution/security and noise proof before hot-path code. | research_route_blocked_for_hot_path |
| S284-E-tail-and-sub-a | Optimize sub_a/NCMUX/extract residuals. | All are low-share in the selected candidate profile. | Amdahl impact is small unless combined with a broader schedule change. | Likely neutral if pursued alone. | Reopen only after a new profile shows larger share. | deferred |

## Promotion Rule

A candidate is promoted only if it passes:

1. isolated equivalence for every affected lane/state transition;
2. complete-SAB correctness;
3. repeated `T_bootstrap/r` A/B against the current best same-backend control;
4. noise/resource reporting;
5. native or explicitly scoped platform provenance when making target claims.
