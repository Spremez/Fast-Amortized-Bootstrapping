# Stage 65A R4 Unrolled AVX512 Variant Plan

Date: 2026-06-26

## Objective

Evaluate one local optional Stage65 variant without changing the scalar SAB
baseline or the default promoted PVW/MAT-SAB path:

```text
MAT_TRGSW_AVX512_R4_UNROLLED_ROWS=true
```

The variant is limited to `k=1,l=1,r=4` AVX512 MAT external product code. It
keeps the same dense MAT arithmetic and key layout while explicitly hoisting row
pointers and unrolling MAT rows 1-4.

## Hypothesis

Explicit r=4 row unrolling may reduce hot-loop pointer chasing and small-loop
overhead in the MAT external product. Because dense `(1+r)^2` arithmetic remains
unchanged, expected gains are modest and must be verified at complete-SAB level.

## Gates

Correctness:

- baseline and `r4_unrolled` staged `SAB_PVW_KERNEL_TEST=true` must pass;
- if full-SAB smoke is run, both variants must pass
  `SAB_PVW_BENCH correctness target_full`.

Performance:

- collect r=4 `MAT_TRGSW vs scalar` and `MAT_TRGSW_FULL vs scalar_full`;
- collect r=4 complete-SAB smoke if `STAGE65_FULL_SAB_RUNS>0`;
- compare only same backend, same parameter, same active-buffer flags.

Instruction proxy:

- collect `objdump` FMA/vector-move counts for `build/mattrgsw.o` and
  `build/polynomial.o`;
- treat these counts as proxy evidence only, not native hardware-counter proof.

Promotion policy:

- one-run full-SAB smoke can only yield
  `SMOKE_POSITIVE_PENDING_REPEATED_NOISE_RESOURCE`;
- promotion requires repeated full-SAB A/B, correctness/noise, resource, and
  Stage42 closure refresh;
- neutral/negative results remain as ablation evidence.

## Primary Command

```bash
STAGE65_KERNEL_RUNS=1 \
STAGE65_FULL_SAB_RUNS=1 \
STAGE65_OUT_DIR=repro/stage65_r4_unrolled_avx512 \
bash scripts/run_stage65_r4_unrolled_avx512.sh

python scripts/build_stage65_r4_unrolled_avx512_log.py
```

## Failure Handling

- correctness fails: reject the variant and do not benchmark longer;
- kernel is neutral/negative: record as ablation and do not run repeated
  full-SAB;
- kernel is positive but full-SAB is neutral/negative: keep kernel-only result,
  do not claim bootstrapping acceleration;
- full-SAB smoke is positive: schedule repeated A/B plus noise/resource gates
  before any promotion.
