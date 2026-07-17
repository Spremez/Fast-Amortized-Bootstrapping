# Current MAT-SAB CCS/USENIX Goal

The controlling contract is
`docs/superpowers/specs/2026-07-16-ccs-usenix-mat-sab-research-contract-design.md`.

The objective is a source-testable r-body MAT-RLWE SAB algorithm whose complete
bootstrapping latency per plaintext lane, `T_bootstrap/r`, beats both repeated
scalar SAB and the current exact-dense PVW/MAT-SAB baseline under the contract's
correctness, security-scope, noise, resource, statistical, literature, and
artifact gates.

The exact-dense implementation and its measured speedups remain a baseline,
not Goal completion. Candidate exploration is finite: A (Star-Cycle Sparse
MAT-GGSW), then B (Factorized Star-Cycle), then C (Rank-Bounded Shared-Mask
State). The active state and budgets are recorded in `research_state.yaml`.

No production hot-path change is allowed before the active candidate passes
the mechanism, key/security/noise, and Amdahl gates. Conference acceptance is
external; the repository-controlled success state is `PAPER_READY`.
