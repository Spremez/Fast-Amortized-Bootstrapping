# V118: Lane-Local Real-Type Design

## Summary

- Parent algorithm: 2025/686 binary sparse amortized bootstrapping with local PVW/MAT-SAB batching.
- Focused module: MAT-RLWE/r-body external-product representation.
- Optimization target: amortized complete-SAB latency `T_bootstrap/r`.
- Status labels: `[theory-partial]`, `[experiment-gated]`, `[not-hot-path]`.
- Main hypothesis: lane-local type design can preserve Stage116 arithmetic while reducing dense selector terms.

## Mathematical Definition

For k=1 and r lanes, define a lane-local accumulator with one mask/body
pair per lane, giving `2r` polynomial components. Define a selector
skeleton with one shared term and two lane-local terms per lane, giving
`1+2r` product terms and `2(1+2r)` conservative DFT polynomials.

## Pseudocode

```text
Input: r lane count, N polynomial dimension
Output: lane-local type shape and gate status
1. Allocate conceptual accumulator fields mask[q], body[q].
2. Allocate conceptual selector fields shared plus lane_mask[q], lane_body[q].
3. Check no off-lane body fields exist.
4. Check key secret polynomial count equals r for k=1.
5. Record noise/key unknowns and stop before hot-path integration.
```

## Delta From Original Algorithm

| Original component | Variant component | Relationship | Evidence/status |
| --- | --- | --- | --- |
| shared-mask PVW_TMLWE `1+r` accumulator | lane-local `2r` accumulator | changes data structure | Stage118 design gate |
| dense MAT selector `(1+r)^2` polys | compact selector `2(1+2r)` polys | reduces term/storage model | Stage117-118 |
| current PVW key `r` lane secrets | same `r` lane secrets | intended key reuse | must be verified by Stage119 |

## Complexity Change

- Time: target external-product terms change from `(1+r)^2` to `1+2r`.
- Memory: accumulator grows from `1+r` to `2r`; selector storage shrinks for r>=4.
- What must be measured: real allocation, phase equivalence, noise, DFT conversion, and complete-SAB timing.

## Theory Dependencies

- Inherited assumptions: binary SAB schedule and lane-independent outputs.
- New assumptions: lane-local mask encryption preserves phase and security.
- Proof steps affected: selector encryption, external product correctness, extract/KS compatibility, noise accumulation.
- Current status: design gate passed; proof and real-object evidence missing.

## Potential Failure Reasons

- Real encryption cannot preserve the lane-local invariant.
- Noise or key switching grows beyond scalar/PVW baseline.
- DFT layout or AVX512 implementation loses the product-count advantage.
- Complete SAB schedule reintroduces dense cancellation.

## Required Experiments

- Baselines: dense shared-mask PVW/MAT and repeated scalar SAB.
- Metrics: phase mismatches, noise gap, key/RSS ratio, `T_bootstrap/r`.
- Ablations: r=2/4 first, then r=6 if real-object gates pass.
- Success criteria: real-object phase/noise pass before any hot-path code.
- Failure criteria: any phase mismatch, unexplained noise growth, or memory blowup.

## Paper Contribution Candidate

A lane-local MAT-RLWE SAB representation may reduce body-output external
product terms `[theory-partial][experiment-gated]`. It is not paper-ready
until real-object, noise, complete-SAB, and related-work gates pass.
