# Algorithm Variant: H13 MAT Body Reduction Design

Date: 2026-06-26

## Scope

H13 is a design gate for future local PVW/MAT-SAB optimization after Stage82.
It is not a promoted algorithm and not a hot-path change.

The target path is:

```text
binary SET_2_3_2048
spqlios_avx512
SAB_PVW_ACTIVE_BUFFER_FUSION=true
MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true
MAT_TRGSW_AVX512_RGT4_FUSED=true for the experimental r=6 branch
```

## Selected Preflight Candidate

Candidate:

```text
H13-C1-r6-full-output-tile-sweep
```

Algorithm idea:

1. Keep the same `MAT_TRGSW_DFT` key layout and PVW ciphertext format.
2. Add an explicit r=6-only MAT body preflight path.
3. For each coefficient block, accumulate all seven outputs for the same
   dec-row stream before advancing the coefficient.
4. Compare against the current r>4 fused kernel that uses output tiles of 4.
5. Reject if register pressure or spills erase the dec-row reuse benefit.

Expected local effect:

```text
dec-row vector load units per coefficient:
current r=6 tiled path = 28
full-output r=6 tile   = 14
```

Expected unchanged costs:

```text
dense row-output interactions = 49
selector vector loads remain dense
from_DFT/add/sub schedule remains unchanged
key size and key format remain unchanged
```

## Required Stage84 Gates

Correctness:

- isolated r=6 MAT/PVW identity-lane correctness;
- no scalar SAB behavior change;
- target full-output correctness before any performance claim.

Performance:

- same-backend DFT-output and full-output MAT microbench;
- objdump spill/load sanity check;
- native perf counters if available, but WSL timing alone is acceptable only
  for preflight, not theoretical optimality;
- non-instrumented complete-SAB A/B only if the kernel microbench is positive.

Promotion:

- no default path change in Stage84;
- promotion requires a later full-SAB repeated/noise/resource campaign;
- if full-SAB is neutral, keep as an ablation and return to the candidate
  matrix.

## Blocked Candidate

Sparse selector skipping is blocked. It may reduce dense arithmetic in theory,
but it would require exposing or encoding selector structure beyond the current
encrypted `MAT_TRGSW_DFT` semantics. That is a key-format and security problem,
not a local kernel optimization.
