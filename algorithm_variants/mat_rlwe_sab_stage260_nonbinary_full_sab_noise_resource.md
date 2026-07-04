# MAT-RLWE SAB Stage260 Non-Binary Full SAB Noise/Resource

Stage260 keeps the Stage259 full non-binary path and adds a falsifiable
multi-trial gate:

```text
for mode in include_zero, ternary:
  for r in 1,2,4:
    run full PVW/MAT SAB and repeated scalar SAB for 3 trials
    record final output noise against LUT expectation
    record PVW-vs-scalar pair noise at body and post-processing stages
    record non-binary selector key-size and keygen estimates
```

The algorithmic object remains MAT-RLWE/r-body ciphertext SAB. The result
admits target performance preflight only; it does not prove speedup.

Stage260 gate: `PASS_STAGE260_NONBINARY_FULL_SAB_NOISE_RESOURCE`.
