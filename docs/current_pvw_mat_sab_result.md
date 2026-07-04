# Current PVW/MAT-SAB Result

Input head: `acd7112`.

Supported claim: exact PVW/MAT-SAB improves complete SAB amortized throughput
by about `1.745361x` under the recorded r=4 target path, measured as
`T_bootstrap/r` versus repeated scalar SAB.

Important boundaries:

- metric is per-lane amortized throughput, not single scalar bootstrap latency;
- exact dense/local-layout routes are closed under current evidence;
- selector-transpose reached only `1.028925x` isolated dense speedup
  and `1.006006x` projected full-SAB speedup, so it is not
  promoted;
- compact/structured product-count reduction remains proof-blocked;
- no theoretical optimality or all-parameter claim is supported.

Primary evidence:

- `repro/stage321_r4_unrolled_fullsab_ab/perf_summary.csv`
- `repro/stage325_selector_transpose_resource_probe/summary.csv`
- `repro/stage326_exact_dense_route_closeout/summary.csv`
- `repro/stage327_final_claim_repro_refresh/summary.csv`
