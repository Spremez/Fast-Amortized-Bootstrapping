# Stage148 H14 Repeated Statistical Model

Date: 2026-07-03

The repeated gate tests whether Stage147's current-head smoke survives process-level variance. The endpoint remains amortized MAT-RLWE/SAB throughput:

```text
T_lane = T_bootstrap / r
speedup_backend_vs_wrapper = T_lane(wrapper) / T_lane(backend)
speedup_backend_vs_scalar = T_scalar_repeated / T_backend
```

A backend route is promotable only if repeated full-SAB timing is positive and final-output noise/resource gates pass. A local materialization improvement or one-run smoke remains insufficient.
