# Stage224 Exact PVW/MAT AVX Resource Model

The exact PVW/MAT path is the only currently admitted complete-SAB route. Stage224
therefore measures the explicit r=6 backend path by

```text
T_lane = T_bootstrap / r
speedup_vs_scalar = T_scalar_repeated / T_pvw_batch
```

The backend-vs-wrapper comparison isolates the AVX/materialization path within
the same exact MAT/PVW algorithm. Noise/resource are side conditions, not part
of the latency numerator.
