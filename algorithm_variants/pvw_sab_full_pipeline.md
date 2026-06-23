# Variant: Full PVW SAB Pipeline

Date: 2026-06-23

## Objective

Move beyond PVW blind-rotation batching and make the complete SAB
post-processing path multi-body aware.

## Current Pipeline

```text
PVW setup/blind rotation
-> PVW extract
-> materialize each body as scalar TLWE
-> scalar packing KS per lane
-> scalar HW-reducing KS per lane
```

## Proposed Pipeline

```text
PVW setup/blind rotation
-> PVW extract
-> PVW packing KS
-> PVW HW-reducing KS
-> materialize only at final output boundary
```

## Expected Complexity Change

Current post-processing tail:

```text
T_post_current(r) = r * (T_materialize + T_packing_KS + T_HW_KS)
```

Target post-processing tail:

```text
T_post_pvw(r) = T_pvw_extract + T_pvw_packing_KS(r) + T_pvw_HW_KS(r)
```

The target is not automatically sublinear; it must reuse decomposition,
memory movement, or DFT transforms across bodies. A naive PVW key-switch that
just wraps scalar loops will not be accepted as an algorithmic improvement.

## Correctness Invariant

For each lane `q` and output coefficient:

```text
phase(out_pvw.body[q]) == phase(out_scalar[q])
```

The comparison must hold after:

- blind rotation;
- extraction;
- packing key switch;
- HW reducing key switch;
- final full SAB output.

## Required Experiments

- staged correctness at small parameters for `r=1/2/4`;
- target correctness for binary `SET_2_3_2048`;
- final-output noise sweeps for `r=2/4`;
- full SAB A/B against repeated scalar SAB;
- key size, keygen time, and RSS comparison.
