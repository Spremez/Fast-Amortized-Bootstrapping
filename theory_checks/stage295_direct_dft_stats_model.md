# Stage295 Stats Refresh Model

Stage295 keeps the comparison dimension fixed:

```text
complete SAB T_bootstrap / r
```

for selected-control PVW-SAB and the direct-DFT candidate. It also reruns the
target final-output scalar-equivalence noise gate. This separates:

- algorithm-level amortized throughput versus repeated scalar SAB;
- incremental direct-DFT benefit over the selected PVW-SAB control;
- final-output correctness/noise side condition.

The stage is a local statistical refresh, not a universal optimality proof.
