# V119: Vector-Shared Lane-Local Object

## Summary

- Parent algorithm: PVW/MAT-SAB r-body research track.
- Focused module: lane-local body-linear external product representation.
- Optimization target: `T_bootstrap/r` after complete SAB integration.
- Status labels: `[object-semantics-supported]`, `[noise-toy-only]`, `[not-hot-path]`.
- Main hypothesis: vector-shared lane-local storage can support independent LUT lanes while preserving body-linear term reduction.

## Mathematical Definition

For each lane q, store a lane-local shared-row encryption and a lane-local
body-row encryption. The scalar-shared interpretation is rejected because
it cannot encode lane-dependent shared-row messages.

## Pseudocode

```text
Input: lane q, coefficient i
Output: phase matching dense reference
1. decrypt shared_q[i] with lane q key
2. decrypt body_q[i] with lane q key
3. return d_shared[i] * phase(shared_q[i]) + d_body[q,i] * phase(body_q[i])
```

## Delta From Stage118

| Stage118 interpretation | Stage119 refinement | Status |
| --- | --- | --- |
| scalar shared term possible | rejected for independent LUT lanes | negative control passes |
| conservative selector `2(1+2r)` | vector-shared selector `4r` | phase-supported in toy C |
| noise recorded-not-proven | toy digit-sum noise bound checked | real noise still required |

## Required Experiments

- real struct allocation and destructor tests;
- real polynomial phase equivalence;
- real encryption/noise simulator;
- DFT conversion prototype;
- only then isolated external-product kernel work.
