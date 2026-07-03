# MAT-RLWE SAB Amortized Optimality Check

Date: 2026-07-03

## Claim Under Study

The target claim is not merely that the current implementation is faster. The
target claim is:

```text
Using an r-body MAT-RLWE ciphertext, SAB can be optimized so that the complete
bootstrap latency per processed plaintext bit/lane is minimized under the
2025/686 SAB schedule and the chosen backend.
```

Current status:

```text
[theory gap open][experiment partially supported][do not claim optimality]
```

## Baseline Model

For the binary `SET_2_3_2048` target used in the current evidence:

```text
h = 39
rho = r_prec = 7
N = 2048
S = (h + 1) * rho * N = 573440
```

Scalar repeated baseline for `r` lanes:

```text
T_scalar_repeat(r) = r * (S * C_scalar_cmux + T_tail_scalar)
A_scalar(r) = T_scalar_repeat(r) / r
```

MAT-RLWE SAB path:

```text
T_mat(r) = S * C_mat_cmux(r) + T_tail_mat(r)
A_mat(r) = T_mat(r) / r
```

The valid speedup endpoint is:

```text
speedup_amortized(r) = A_scalar(r) / A_mat(r)
                     = T_scalar_repeat(r) / T_mat(r)
```

This equality only holds when both sides process the same `r` lanes.

## Lower-Bound Structure

A useful lower bound must separate:

1. shared SAB schedule cost;
2. selector/key stream cost;
3. decomposition and DFT materialization cost;
4. unavoidable per-body arithmetic;
5. memory load/store lower bound;
6. extract/post-processing tail.

A candidate lower-bound form is:

```text
T_lower(r) =
  S * (C_shared_schedule + C_selector_stream)
  + S * r * C_unavoidable_body
  + T_tail_lower(r)
```

Then:

```text
A_lower(r) = T_lower(r) / r
gap(r) = A_impl(r) / A_lower(r)
```

The current project has not yet closed `gap(r)` numerically.

## Dense MAT Risk

If `C_mat_cmux(r)` grows approximately as `r^2`, the amortized cost

```text
C_mat_cmux(r) / r
```

can grow with `r`, preventing optimal scaling. Therefore any candidate claiming
MAT-RLWE SAB optimality must demonstrate that the hot external product and
schedule cost are closer to body-linear than dense-matrix quadratic behavior
for the relevant `r`.

## Required Proof/Measurement Gates

1. Derive a per-CMUX operation model for the implemented MAT external product.
2. Compare body-linear, tiled, and dense MAT variants under identical SAB
   schedule counts.
3. Record AVX512 load/store/FMA counters on native Linux for at least one
   promoted candidate.
4. Report complete-SAB `T_total/r`, not only kernel throughput.
5. Show correctness/noise/resource gates before interpreting speedup.

## Current Evidence

- Stage36 supports amortized complete-SAB improvement for r=2/r=4.
- Stage88 supports an explicit r=6 candidate with 3-run evidence only.
- Stage101 provides hardware-counter attribution evidence but not optimality.
- Stage105 confirms the previous scoped engineering package is complete.

## Current Boundary

Allowed:

```text
The current PVW/MAT-SAB path improves complete-SAB amortized latency for the
tested binary target under the recorded backend and gates.
```

Blocked:

```text
The current path is theoretically optimal.
The current path is optimal for all r.
The current path is a universal MAT-RLWE SAB algorithmic optimum.
```

