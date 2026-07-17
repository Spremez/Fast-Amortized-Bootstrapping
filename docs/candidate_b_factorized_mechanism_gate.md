# Candidate B Factorized Mechanism Gate

Decision: `REJECT_CANDIDATE_B_EXACT_STANDARD_PVW_FACTORIZATION_ROUTE_TO_C`.

The exact current standard-PVW selector is

```text
C = mu h I + v w^T + [0 | E].
```

The phase identity passes for r=2/4/6 and mu=0/1, including a hand-derived
r=2 orientation oracle. Explicit 128-bit inputs to the current normal-sampler
formula produce both even and odd Torus outputs. The map
`phi(f)=f(1) mod 2` is a ring homomorphism from the finite ring
`(Z/2^64Z)[X]/(X^N + 1)` to GF(2). Independent coefficient sampling therefore supports a parity-pattern
error witness whose image has rank r, while every q<r ring factorization has
image rank at most q. The constructed rank-q image controls pass, so the
rejection is not caused by a checker that rejects all factorizations.

Factoring only the noiseless rank-one term leaves `(r+1)r` dense error
products. The recorded q=r count is for generic dense two-sided factors, not
a universal arithmetic lower bound.

No concrete encrypted-factor/relinearization or closed lane-pair
conversion satisfying the complete cost gate is registered.

Production hot-path permission remains `false`. Candidate C is the next
finite route. Existing scalar and exact-dense PVW/MAT-SAB implementations are
unchanged.

## Primary-Source Boundary

- 2025/686 target SAB, locally reviewed full-text anchors:
  https://eprint.iacr.org/2025/686
- Common-mask ciphertext and CM-GGSW prior art:
  https://eprint.iacr.org/2025/2112
- Packed/PVW and standard TFHE sources are metadata/background scoped:
  https://eprint.iacr.org/2012/565 and
  https://eprint.iacr.org/2018/421

The local Stage102 and Stage335 logs contain the reviewed full-text claim
anchors. The PVW and TFHE rows are used only for background positioning. The
standard common-mask GGSW realization retains a quadratic `(k+r)^2` lane
factor. No checked source supplies the complete Candidate B conjunction.
This is not a general impossibility theorem and is not a novelty proof.

## Claim Boundary

This result rejects the tested exact factorization of the current independent
PVW row distribution. It is not a general impossibility theorem for every
structured key, correlated-error assumption, or redesigned accumulator.
