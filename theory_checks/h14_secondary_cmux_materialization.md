# H14 Secondary CMUX Materialization Theory Check

Date: 2026-06-26

## Target

Parent path: explicit PVW/MAT-SAB binary path with active-buffer fusion and
H11 r>4 fused MAT evidence kept experimental.

Focused module: CMUX/NCMUX materialization after MAT external product inside
`sab_pvw_RGSW_monomial_mul_state`.

## Observed Bottleneck

Stage82 records the r=6 profile with exact SAB schedule counts:

```text
CMUX/MAT EP = 573440
NCMUX       = 5080
sub_a       = 39
copyback    = 0
```

The same profile records:

```text
MAT EP/full       = 47.6916%
from_DFT/full     = 21.7231%
CMUX add/full     = 13.6870%
CMUX sub/full     = 13.4137%
NCMUX/full        = 1.9022%
non-MAT/full      = 52.3084%
```

Stage84 shows that the H13 r=6 full-output MAT tile preflight is only
kernel-positive and does not improve complete SAB. Therefore the next local
search should not assume that more MAT body reshaping is automatically the
dominant full-SAB route.

## Current CMUX Equation

For a PVW accumulator sample:

```text
tmp_torus = in2 - in1
tmp_dft   = MAT_TRGSW_DFT * tmp_torus
out       = in1 + FromDFT(tmp_dft)
```

The current code already has a wrapper-level `pvmtmlwe_from_DFT_add()` path.
That path still calls `polynomial_DFT_to_torus()` first and then performs an
AVX512 torus add pass. Stage18 and Stage23 show that this wrapper/epilogue
fusion is correct but neutral for complete SAB.

## Theory Boundary

Any Stage86 candidate must be distinct from Stage18/23:

- it may change the polynomial/backend materialization boundary;
- it may change a schedule-window lifetime if memory and count models support
  it;
- it must not inspect plaintext selectors;
- it must not change MAT key format;
- it must not change scalar SAB default behavior.

## Candidate Conclusions

### H14-C1: Backend FromDFT-Add Callback

Selected for preflight.

Mechanism: add a backend-level inverse-DFT-to-torus plus addend callback so the
add-back is applied during final materialization rather than as a second torus
polynomial pass.

Potential gain is constant-factor and memory-traffic oriented. The upper bound
is limited by Stage82 shares:

```text
from_DFT + add = 35.4101% of full body
add only       = 13.6870% of full body
```

Removing the whole add pass has an Amdahl ceiling near `1.159x` at body level,
but a real backend callback may remove only output reread/write traffic, not
FFT arithmetic.

### H14-C2: DFT-Lazy Bit Window

Rejected for now. It does not reduce inverse DFT count because the next SAB bit
needs torus-domain inputs. It also requires large DFT temporary arrays across
many accumulator slots and risks cache/RSS regressions.

### H14-C3: Dual Butterfly Shared-Input Wrapper

Kept as a fallback. It targets `CMUX sub/full = 13.4137%`, so even halving the
sub stage has a small Amdahl ceiling. It should only be tested after H14-C1 or
if future profiles increase sub share.

### H14-C4: Repeat Stage23 R6 Schedule Fusion

Rejected because it repeats an epilogue-only mechanism that Stage23 already
classified as neutral.

### H14-C5: NCMUX Automorphism First

Rejected because Stage82 shows NCMUX is only `1.9022%` of full body.

## Required Proof/Experiment Gate

H14-C1 can only support a claim after:

- identity-lane correctness for the backend callback;
- r=4/r=6 materialization microbench against current `pvmtmlwe_from_DFT_add`;
- complete SAB A/B under the same backend;
- noise/resource gates if complete SAB is positive;
- Stage42/51/57/59/68 closure refresh.

Until then, H14 remains `[experiment pending]` and `[implementation-only
constant-factor hypothesis]`.
