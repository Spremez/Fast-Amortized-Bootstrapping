# Stage294 Target Noise Model

The direct-DFT optimization changes the sub-decompose representation path but
not the plaintext LUT semantics, selector schedule, or scalar reference. The
target final-output noise gate therefore compares:

```text
PVW/MAT-SAB direct DFT output lane q
vs repeated scalar SAB output q
vs expected LUT(input)
```

for every coefficient and every body lane. The repeated scalar SAB output is
the correctness reference for the nonbinary packed LUT; the hand-written LUT
model is retained only as a diagnostic because nonbinary packing has additional
encoding semantics. Passing this gate supports scalar-equivalent final-output
correctness/noise for the target slice; it does not prove stage-wise noise or
all-parameter behavior.
