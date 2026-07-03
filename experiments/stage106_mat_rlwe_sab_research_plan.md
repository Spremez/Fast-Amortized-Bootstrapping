# Stage106 MAT-RLWE SAB Research Plan

Date: 2026-07-03

## Objective

Reframe PVW/MAT-SAB as an algorithmic MAT-RLWE SAB research program.
The primary endpoint is:

```text
A_mat(r) = T_complete_bootstrap_mat(r) / r
```

where `r` is the number of processed independent plaintext lanes/bits in one
MAT-RLWE ciphertext with shared mask and `r` bodies.

## Fixed Comparison

Every complete-SAB comparison must use:

- same target parameter set;
- same FFT/backend family;
- same processed lane count `r`;
- scalar repeated baseline processing `r` independent lanes;
- total latency and per-lane latency;
- correctness/noise/resource gates before performance promotion.

The existing Stage36 speedups are valid amortized comparisons because both
sides process the same `r` lanes:

```text
speedup = T_scalar_repeated(r) / T_mat(r)
        = (T_scalar_repeated(r)/r) / (T_mat(r)/r)
```

## Research Loop

1. Hypothesis
   - State the exact MAT-RLWE SAB algorithmic change.
   - Name the expected reduction: schedule sharing, body-linear MAT external
     product, DFT materialization reduction, layout locality, or tiling.
2. Theory model
   - Update the `T_scalar_repeat(r)` and `T_mat(r)` formulas.
   - State whether the improvement is asymptotic, constant-factor,
     memory-traffic, or implementation-only.
3. Runnable implementation gate
   - If the change affects only MAT external product, run kernel microbench.
   - If it affects CMUX/RGSW/sparse schedule, run staged equivalence first.
   - If staged gates pass, run complete-SAB A/B.
4. Correctness/noise/resource gate
   - Run deterministic equivalence.
   - Run multi-seed final-output noise.
   - Record key size, keygen time, RSS, and memory overhead.
5. Stats gate
   - For paper-level performance claims, use at least 10 complete-SAB samples
     for the target `r` and report mean/min/max/stddev/CI.
6. Promote/neutral/reject
   - Promote only if complete-SAB `T_total/r` improves and resource overhead is
     acceptable.
   - Mark neutral if kernel wins but complete-SAB does not.
   - Reject if correctness, noise, or resource gates fail.

## Stop Rules

- Do not spend more than two consecutive stages on theory without a runnable
  microbench or complete-SAB gate.
- Do not claim theoretical optimality until a lower-bound model and measured
  load/store/FMA gap are recorded.
- Do not promote r=6 or r>6 as paper-level evidence from 3-run candidate data.
- Do not compare PVW/MAT total time to a single scalar lane; compare equal
  processed lane count.

## Immediate Next Gate

Start with V106-B or V106-D:

- V106-B: body-linear MAT external product for independent SAB lanes.
- V106-D: body-major coefficient-blocked layout for AVX512 load/store locality.

Both must report:

```text
kernel C_mat_cmux(r)/r
complete-SAB T_total/r
load/store/FMA counters when available
correctness/noise/resource status
```

