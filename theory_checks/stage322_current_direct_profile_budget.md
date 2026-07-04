# Stage322 Current Direct Profile Budget

Stage322 is a routing profile, not a speed claim. It measures the current
direct PVW/MAT-SAB path with body, MAT split, and direct-DFT profile counters.

The routing rule is deliberately conservative:

```text
if copyback_share >= 2%: test copyback fusion
elif sub_a_share >= 5%: test sub_a rotation/copy
else if dense_from_dec is the largest unclosed MAT component: test dense MAT layout/counters
```

Digit and IFFT routes are closed by prior stages. The exact r4-unrolled route
is closed by Stage321. Selecting dense MAT layout does not claim that a new
kernel will work; it only admits a counter/microbench preflight.
