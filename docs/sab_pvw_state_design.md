# Stage 4 SAB-PVW Lane State Design

Date: 2026-06-11

## Purpose

Stage 4 introduces an isolated PVW/MAT_TRGSW CMUX path for SAB lane-state
validation. It does not replace `sab_rlwe_bootstrap` and it does not change the
scalar SAB default path.

The goal is to verify the central batching invariant needed by the later
`sab_pvw_*` integration:

```text
phase(acc_pvw.body[q]) == phase(acc_scalar[q])
```

for every lane `q` after each isolated CMUX/NCMUX step.

## Lane Model

The first `sab_pvw_*` interpretation of `r` is:

```text
r = number of independent LUT / SAB lanes batched in one PVW accumulator
```

It is not accumulator-index packing. Each lane has its own body polynomial and
its own scalar reference accumulator. All lanes share the input/mask flow used by
the PVW/MAT_TRGSW external product.

The lane state is:

```text
PVW accumulator:
  a[0..k-1]      shared mask polynomials
  b[0..r-1]      body lanes

Scalar references:
  lane q:
    a[0..k-1]    copied from PVW shared mask
    b            copied from PVW body q
```

The selector state is:

```text
PVW selector:
  MAT_TRGSW_DFT over a PVW key with k shared mask components and r bodies

Scalar reference selector:
  one TRGSW_DFT per lane q, generated from the corresponding scalar lane key
```

The isolated CMUX operation is:

```text
CMUX(A, B, S) = A + S * (B - A)
```

The PVW implementation evaluates `S * (B - A)` with
`mat_trgsw_mul_pvmtmlwe_DFT`, while the scalar reference evaluates the same
operation lane-by-lane with `trgsw_mul_trlwe_DFT`.

## Stage 4 Test Scope

The Stage 4 executable check covers:

```text
r = 1, 2, 4
CMUX selector = 0
CMUX selector = 1
NCMUX selector = 0
NCMUX selector = 1
```

For CMUX, the inputs are encrypted PVW samples and copied scalar lane samples.

For NCMUX, the current isolated check uses trivial/noiseless inputs and applies
the raw `X -> X^{-1}` polynomial automorphism before CMUX. This validates the
lane layout, selector batching, and body phase equivalence for the NCMUX branch
without depending on a PVW automorphism keyswitch implementation. Full encrypted
NCMUX compatibility remains a Stage 5/6 integration requirement because the
scalar SAB path currently uses `trlwe_eval_automorphism(..., aut_minus1)`.

## Correctness Gate

The Stage 4 gate passes only if every lane decrypts to the same torus message as
its scalar reference after each checked step:

```text
torus2int(phase_pvw[q][i], prec) == torus2int(phase_scalar[q][i], prec)
```

for all lanes `q` and coefficients `i`.

The check must be deterministic enough to run as a smoke test and must not
modify the production scalar SAB entrypoint.

## Performance Gate

Stage 4 is primarily a correctness and state-design stage. Its performance gate
is limited to ensuring the isolated path uses the existing MAT external product
scratch object and does not allocate in the repeated CMUX hot step.

Full latency and throughput claims are deferred until Stage 7, after the
`sab_pvw_*` path is connected to the complete SAB bootstrapping flow.

## Failure Handling

If Stage 4 fails:

1. First check whether the failure is in `r=1`. A failure there means the MAT
   external product or lane copy model has regressed.
2. If only `r>1` fails, inspect shared-mask/body indexing and MAT row ordering.
3. If only NCMUX fails, keep CMUX accepted and treat PVW automorphism/key-switch
   support as the blocking issue for Stage 5.
4. Do not change or replace `sab_rlwe_bootstrap` while resolving Stage 4.

## Stage 5 Handoff

Stage 5 can start only after this isolated invariant is stable. The next
integration steps are:

```text
CMUX lane state -> RGSW_monomial_mul lane state -> sparse_mul -> sab_pvw_*
```

The scalar SAB path remains the correctness oracle throughout that process.
