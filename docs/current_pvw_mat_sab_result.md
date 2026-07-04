# Current PVW/MAT-SAB Result

Input evidence head: `6a5f113`.

Supported scoped claim: direct PVW/MAT-SAB improves complete SAB amortized
throughput by `1.747647x` for
`BINARY SET_2_3_2048`, include-zero, `r=4`, `spqlios_avx512`, measured as
`T_bootstrap/r` versus repeated scalar SAB.

Primary current-head result:

- PVW/MAT-SAB `T_bootstrap/r`: `6117083.425` us
  with 95% CI `6073694.765..6160472.085` us;
- repeated scalar SAB `T_bootstrap/r`: `10690503.200` us;
- complete PVW run processes `r=4` lanes, so total PVW time is `24468333.700` us
  and repeated scalar total is `42762012.800` us;
- correctness: `Pass`, samples: `10`;
- final-output noise/equivalence: `0/10` pair failures;
- max RSS: `2415796` KB.

Important boundaries:

- metric is per-lane amortized complete bootstrapping throughput, not single
  scalar bootstrap latency;
- exact dense/local-layout routes are closed under current evidence;
- selector-transpose reached only isolated/projection-level neutral evidence
  and is not promoted;
- compact/structured product-count reduction remains proof-blocked;
- no theoretical optimality, novelty, or all-parameter claim is supported yet.

Primary evidence:

- `repro/stage331_current_head_highstat_refresh/summary.csv`
- `repro/stage331_current_head_highstat_refresh/perf_summary.csv`
- `repro/stage331_current_head_highstat_refresh/noise_summary.csv`
- `repro/stage332_paper_result_pack/paper_result_table.csv`
