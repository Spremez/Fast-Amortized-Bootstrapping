# V134: Generalized Lane-Pair Input Compact EP

## Summary

- Parent algorithm: PVW/MAT-SAB r-body research track.
- Focused module: closure-capable compact external product.
- Optimization target: complete-SAB amortized `T_bootstrap/r`.
- Status labels: `[isolated-ep]`, `[closure-capable]`,
  `[performance-gated]`.
- Decision: `NEUTRAL_STAGE134_GENERALIZED_INPUT_EP_CORRECT_BUT_PERF_BLOCKED`.

## Complexity Change

- Stage130 first step: one shared mask plus r bodies, decomposition
  count `T*(1+r)`.
- Stage134 iterative closure path: r masks plus r bodies, decomposition
  count `2*T*r`.
- Dense proxy: `(1+r)^2` DFT multiply-add terms.
