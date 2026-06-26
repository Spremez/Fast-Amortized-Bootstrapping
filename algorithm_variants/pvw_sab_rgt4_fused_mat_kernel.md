# Candidate Variant: PVW-SAB R>4 Fused MAT Kernel

Status: implemented behind `MAT_TRGSW_AVX512_RGT4_FUSED`, positive smoke, not promoted

Parent path: explicit `sab_pvw_*` PVW/MAT-SAB

Primary target: `mat_trgsw_mul_pvmtmlwe_DFT`, `k=1`, `l=1`, r=6/r=8

## Hypothesis

The current r>4 generic MAT external-product path loses most of the large-r
amortization benefit because dense MAT multiply/add work becomes dominant. A
dedicated r>4 fused MAT kernel may recover part of the lost scaling by
reusing decomposed/DFT row data across body outputs and by reducing
per-polynomial call, load, and store overhead.

## Proposed Mechanism

- Keep scalar SAB unchanged.
- Keep the current promoted r=2/r=4 path unchanged.
- Add an explicit experimental flag for r>4 fused MAT kernels.
- Implement coefficient-blocked or body-blocked accumulation for r=6/r=8.
- Compare row-major, body-major, and coefficient-blocked update order without
  changing the default key format unless the experiment justifies a separate
  layout path.

## Complexity

The arithmetic complexity remains dense MAT external product:

```text
O((1+r)^2 * l * N)
```

The candidate can only improve constants: fewer repeated loads, fewer stores,
better cache locality, lower helper-call overhead, or better register reuse.

## Stage76 Starting Evidence

Stage76 shows the current generic r>4 path is functional but not promotable:

- correctness smoke passes for r=6/r=8;
- DFT-output MAT vs repeated scalar is `0.984x` for r=6 and `0.912x` for r=8;
- full-output MAT vs scalar-full is `1.168x` for r=6 and `1.044x` for r=8;
- multiply share in MAT shared-mask mode is `55.72%` for r=6 and `61.20%`
  for r=8.

This evidence says the next useful large-r variant must target the multiply
kernel itself. It does not support a claim that current r>4 MAT is already an
optimized complete-SAB acceleration.

## Stage77 Smoke Evidence

Stage77 implements a tiled r=6/r=8 AVX512 kernel behind an explicit flag. The
smoke result is positive but not enough for promotion:

- DFT-output fused/generic is `1.582x` for r=6 and `1.431x` for r=8.
- Full-output fused/generic is `1.510x` for r=6 and `1.370x` for r=8.
- Complete SAB one-run fused/generic is `1.120x` for r=6 and `1.102x` for r=8.
- Complete SAB fused speedup versus repeated scalar is `1.385x` for r=6 and
  `1.290x` for r=8.

r=8 DFT-output remains below repeated scalar (`0.951x`), and the complete SAB
evidence is one-run smoke only. The next gate is repeated full-SAB plus
noise/resource validation, with r=6 as the main candidate and r=8 as a stress
case.

## Correctness Gate

- identity-lane MAT_TRGSW/PVW checks for r=6/r=8;
- staged lane equivalence against scalar reference if wired into SAB;
- full `sab_pvw_*` correctness before any performance claim.

## Performance Gate

- DFT-output microbench against current generic MAT and repeated scalar;
- full-output microbench;
- complete SAB A/B against repeated scalar;
- complete SAB A/B against the current promoted r=4 path when claiming large-r
  improvement;
- repeated runs with mean/min/max and raw logs.

## Promotion Policy

Do not promote if:

- DFT-output speedup remains below 1.0;
- full-output speedup is only low-margin and complete SAB does not improve;
- r=6/r=8 does not beat the current r=4 promoted path under full gates;
- correctness, noise, memory, or key-size gates regress.
