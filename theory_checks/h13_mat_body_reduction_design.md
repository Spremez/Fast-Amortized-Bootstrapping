# H13 MAT Body Reduction Design Check

Date: 2026-06-26

## Starting Point

Stage82 profiles the explicit H11 fused r=6 path and records exact SAB schedule
counts:

```text
CMUX/MAT EP = 573440
NCMUX = 5080
sub_a = 39
active-buffer copyback = 0
```

The same profile attributes the r=6 fused body as:

```text
MAT EP/full = 0.476916
from_DFT/full = 0.217231
add/full = 0.136870
sub/full = 0.134137
non-MAT/full = 0.523084
```

Therefore the next local target is not schedule-count reduction. The schedule
is already invariant and copyback is already eliminated. The remaining local
question is whether the dense MAT body cost per update can be reduced without
changing the key format or leaking selector structure.

## Dense MAT Model

For the target MAT path used here:

```text
k = 1
l = 1
m = k + r = r + 1
rows = outputs = m
```

A dense MAT external product computes all row-output interactions. Its
arithmetic cost per coefficient block is proportional to:

```text
m^2 complex multiply/add operations
```

For r=6, `m=7`, so the dense body has 49 row-output interactions. For r=8,
`m=9`, so the dense body has 81 interactions.

This dense arithmetic is not reduced by tiling. Tiling can only improve
constant factors: dec-row reuse, selector/output locality, helper-call
overhead, and spills.

## Existing R>4 Fused Kernel Limit

The current `MAT_TRGSW_AVX512_RGT4_FUSED` kernel uses `MAT_RGT4_TILE_OUTPUTS=4`.
For r=6, this means two output tiles cover seven outputs. Each dec row is
loaded once per output tile:

```text
current dec vector load units per coefficient = 2 * rows * ceil(outputs / 4)
                                              = 2 * 7 * 2 = 28
full-output tile dec load units              = 2 * rows
                                              = 14
```

The theoretical dec-row load reduction for r=6 is therefore 50%. This does not
reduce selector loads or FMA count, and it may increase register pressure from
8 accumulator vectors to 14 accumulator vectors.

For this reason, a dedicated r=6 full-output tile is a plausible low-risk
preflight candidate, not a guaranteed optimization.

## Full-SAB Bound

Let `p` be the MAT-body share of profiled full body time and `s` be the local
MAT-body speedup. The maximum complete-body multiplier is:

```text
1 / ((1 - p) + p / s)
```

With Stage82 `p = 0.476916`:

```text
s = 1.10 -> 1.045x complete-body multiplier
s = 1.20 -> 1.086x complete-body multiplier
s = 1.50 -> 1.189x complete-body multiplier
```

Any kernel result below this must still be checked by complete-SAB A/B. A
kernel-only win cannot be reported as bootstrapping acceleration.

## Blocked Arithmetic-Count Reduction

The only clear way to reduce dense `m^2` arithmetic is to exploit selector
structure or skip row-output products. The current evaluator receives encrypted
`MAT_TRGSW_DFT` selector ciphertexts. Encrypted zero selector bits remain dense
noisy ciphertext objects, so plaintext skip metadata would require a new
key-format and leakage/security argument.

This blocks sparse selector skipping as a local implementation task. It can be
reopened only with:

- a key-format design;
- a leakage/security argument;
- staged correctness and noise analysis;
- complete-SAB A/B and resource gates.

## Stage83 Decision

The low-risk next preflight is an explicit r=6 full-output tile sweep. It
keeps the current key format and scalar SAB behavior unchanged. It must be
implemented only behind an explicit flag or isolated harness and accepted only
if the kernel signal propagates to non-instrumented complete-SAB evidence.
