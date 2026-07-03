# Stage174 Direct-Scale Model

The current spqlios `execute_direct_torus64_add` path has three coarse phases:

```text
1. scale/copy DFT coefficients into the backend direct buffer
2. run spqlios direct FFT
3. convert doubles to torus and add the torus addend
```

Stage174 modifies only phase 1 under an explicit flag. The theoretical maximum
benefit is bounded by the share of phase 1 inside from_DFT; the FFT and final
torus/add conversion remain unchanged. Therefore a small or neutral result is
expected and must be preserved as evidence.

This is a backend/SIMD optimization. It does not reduce SAB materialization
count, MAT external-product count, or asymptotic complexity.
