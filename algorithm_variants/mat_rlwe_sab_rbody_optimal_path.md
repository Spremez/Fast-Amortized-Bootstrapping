# V106: r-body MAT-RLWE SAB Optimal Path

## Summary

- Parent algorithm: 2025/686 sparse amortized bootstrapping.
- Focused module: complete SAB hot path from blind rotation through
  sparse_mul/RGSW monomial/CMUX/MAT external product and extract.
- Optimization target: amortized complete-SAB latency per processed
  plaintext lane/bit, `T_total/r`.
- Status labels: `[theory gap open] [experiment partially supported] [runnable gates required]`.
- Main hypothesis: replacing repeated scalar RLWE accumulators with an r-body
  MAT-RLWE ciphertext can reduce `T_total/r` by sharing the SAB schedule and
  optimizing body-lane external products, provided the MAT kernel avoids
  dense `r^2` scaling and unnecessary materialization.

## Mathematical Definition

Scalar repeated baseline:

```text
for q in 0..r-1:
  out_q = SAB_scalar(in_q, LUT_q)
```

MAT-RLWE SAB variant:

```text
acc = (a, b_0, ..., b_{r-1})
out = SAB_mat(acc, in_0..in_{r-1}, LUT_0..LUT_{r-1})
```

Primary endpoint:

```text
A_mat(r) = T(SAB_mat producing r outputs) / r
```

Correctness invariant:

```text
phase(body_q(acc_after_step)) == phase(acc_scalar_q_after_same_step)
```

for every lane `q` and every checked CMUX/RGSW/sparse_mul/bootstrap step.

## Pseudocode

```text
Input:
  r independent scalar SAB inputs and LUTs
  MAT_TRGSW_DFT selector keys
  r-body PVW/MAT accumulator

Output:
  r bootstrapped output lanes

1. Pack r LUT accumulators into shared-mask MAT-RLWE state.
2. For each SAB sparse schedule step:
   a. Rotate/subtract active MAT accumulator state as required.
   b. Run RGSW monomial multiplication on the active state.
   c. For each precision bit and coefficient slot, run MAT CMUX/NCMUX.
   d. Carry active buffer/parity instead of forcing copyback after every step.
3. Normalize active state only at API boundary or extract.
4. Extract r output lanes and run post-processing.
```

## Delta From Original Algorithm

| Original component | Variant component | Relationship | Evidence/status |
| --- | --- | --- | --- |
| `r` independent scalar RLWE accumulators | one shared-mask r-body MAT-RLWE accumulator | changes representation | staged equivalence and Stage36/Stage88 evidence |
| scalar `TRGSW x TRLWE` external product | `MAT_TRGSW x PVW_TMLWE` external product | changes hot kernel | implemented, but optimality open |
| forced copyback after monomial state | active-buffer/parity state | reduces schedule traffic | Stage20 positive evidence |
| total scalar repeated runtime | `T_total/r` endpoint | changes evaluation metric | fixed by Stage106 |

## Complexity Change

Time:

```text
scalar repeat: r * S * C_scalar_cmux
MAT path:      S * C_mat_cmux(r)
```

where `S=(h+1)*rho*N` for the binary SAB schedule.

Memory:

```text
MAT key and accumulator bodies grow with r.
The key/RSS overhead must be reported with every speedup claim.
```

What must be measured:

- `C_mat_cmux(r)/r`;
- complete `T_total/r`;
- retired loads/stores;
- AVX512 packed FP events;
- key size, keygen time, RSS;
- noise/failure rate.

## Theory Dependencies

- Inherited assumptions: scalar SAB correctness/noise/parameter assumptions
  from the target implementation and reviewed 2025/686 anchors.
- New assumptions: independent lanes can share schedule/key flow without
  changing each lane phase invariant.
- Proof steps affected: external product correctness, CMUX/NCMUX equivalence,
  active-buffer normalization, extract/post-processing.
- New lemmas needed: body-lane MAT external product equivalence and lower-bound
  gap model for implementation optimality.
- Current status: correctness supported under tested gates; optimality open.

## Potential Failure Reasons

- Dense MAT external product grows like `r^2` and erases amortized gains.
- Extra DFT/fromDFT/materialization traffic dominates body sharing.
- Key size or memory overhead grows faster than throughput benefit.
- r=6/r>6 gains are not statistically stable.
- A layout improvement wins microbench but loses complete SAB.

## Required Experiments

- Baselines: repeated scalar SAB and current active-buffer PVW/MAT-SAB.
- Metrics: total complete-SAB time, per-lane time, speedup, noise failures,
  key size, keygen time, RSS, perf counters.
- Ablations: active-buffer, backend FromDFT-add, body-linear external product,
  layout-only, r-adaptive tiling.
- Complexity runs: r=1/2/4/6/8 where feasible.
- Statistical checks: at least 10 complete-SAB samples for paper-level target
  claims; confidence intervals or equivalent uncertainty reporting.
- Success criteria: complete-SAB `T_total/r` improves over the best recorded
  current path with correctness/noise/resource gates passing.
- Failure criteria: no per-lane improvement, correctness/noise failure, or
  unacceptable key/RSS overhead.

## Paper Contribution Candidate

Conservative candidate:

```text
[experiment partially supported][theory gap open]
We study an r-body MAT-RLWE realization of the 2025/686 SAB hot path and
evaluate complete-SAB amortized latency per processed lane.
```

Not currently allowed:

```text
[do not write]
The implemented MAT-RLWE SAB path is theoretically optimal.
```

