# H10 R>4 Lane Scaling Theory Check

Date: 2026-06-26

## Question

Can PVW/MAT-SAB improve complete bootstrapping throughput by directly raising
the number of independent LUT/SAB lanes beyond the current promoted `r=4`
configuration?

## Mechanism Under Test

PVW/MAT batching amortizes the SAB input/key schedule across multiple body
lanes. Increasing `r` should keep sharing:

- the same sparse selector schedule;
- the same blind-rotation structure;
- the same high-level CMUX/NCMUX sequence;
- one shared mask across multiple body outputs.

The opposing cost is the MAT external product. For the current target
`k=1,l=1`, the dense output update grows with the matrix row/output structure,
and the current hand-specialized AVX512 path is tuned for `r=2` and `r=4`.
For `r>4`, the implementation falls back to the generic MAT path, so dense
arithmetic, register pressure, cache traffic, and output writes can dominate
the saved schedule work.

## Current Evidence

Stage36 r=4 target evidence is the current high-stat reference:

```text
r=4 mean speedup = 1.377x
r=4 95% CI       = [1.314893, 1.438107]
```

Stage74 smoke runs:

```text
r=6 speedup = 1.251x
r=8 speedup = 1.199x
```

Both r>4 smoke runs pass complete-SAB correctness and remain faster than
repeated scalar SAB, but both are below the Stage36 r=4 CI lower bound.

Stage75 profile-diagnosis runs then checked whether the r>4 boundary came
from an accidental schedule/count difference. Both r=6 and r=8 preserved the
target binary SAB counts:

```text
CMUX/MAT EP calls = 573440
NCMUX calls       = 5080
sub_a calls       = 39
copyback calls    = 0
```

The Stage75 profile samples reported:

```text
r=6 speedup = 1.304x, MAT EP/full body share = 0.549836
r=8 speedup = 1.189x, MAT EP/full body share = 0.550237
```

The r=6 profile sample is close to, but still below, the Stage36 r=4 CI lower
bound; r=8 remains clearly below. Since the SAB schedule count is invariant,
the profile supports the dense MAT body/update cost explanation rather than a
schedule-model error.

## Decision

Direct lane-count expansion to `r=6` or `r=8` is not promoted under the
current implementation. The result supports a practical scaling boundary:
small-r PVW/MAT-SAB is useful, while larger-r improvement likely requires a
new r>4-specific layout, register tiling strategy, cache/register blocking
strategy, or sparse/structured MAT design.

## Claim Boundary

This is one-run smoke evidence, not a high-stat performance claim. It can
justify rejecting direct r>4 promotion and planning a future r>4-specific
kernel hypothesis. Stage75 adds profile-backed attribution, but it still
cannot justify broad large-r scalability, theoretical optimality, or
paper-level novelty claims.
