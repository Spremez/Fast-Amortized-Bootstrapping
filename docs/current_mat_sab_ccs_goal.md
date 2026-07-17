# Current MAT-SAB CCS/USENIX Goal

The controlling contract is
`docs/superpowers/specs/2026-07-16-ccs-usenix-mat-sab-research-contract-design.md`.

The objective is a source-testable r-body MAT-RLWE SAB algorithm whose complete
bootstrapping latency per plaintext lane, `T_bootstrap/r`, beats both repeated
scalar SAB and the current exact-dense PVW/MAT-SAB baseline under the contract's
correctness, security-scope, noise, resource, statistical, literature, and
artifact gates.

The exact-dense implementation and its measured speedups remain a baseline,
not Goal completion. Candidate A is frozen as rejected for direct `4r`
star-cycle support under current standard-PVW independent row randomization.
Candidate B is frozen as rejected for exact `q<r` factorization of the same
distribution: a supported parity-evaluation image has rank `r`, and factoring
only the noiseless term leaves Theta(r^2) dense error work. These are scoped
mechanism rejections, not general compact-MAT impossibility results.

Candidate C (Rank-Bounded Shared-Mask State) is the sole active candidate. Its
finite question is whether

```text
a_q = a_shared + sum_{t=1..rho} lambda[q,t] * delta_a[t]
```

with fixed `rho<=2` remains closed across enough CMUX/NCMUX, RGSW monomial,
`sparse_mul`, and `sub_a` steps that a public-schedule batched
relinearization amortizes, preserves every lane phase, and leaves a positive
complete-SAB `T_bootstrap/r` projection against exact-dense PVW/MAT-SAB.
Immediate rank growth to `r`, per-CMUX relinearization, or a nonpositive
complete-cost projection rejects C before production implementation.

No production hot-path change is allowed before the active candidate passes
the mechanism, key/security/noise, and Amdahl gates. Conference acceptance is
external; the repository-controlled success state is `PAPER_READY`.
