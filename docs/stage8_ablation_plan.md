# Stage 8 Ablation and Variant Plan

Date: 2026-06-11

## Objective

Stage 8 decides why the current `sab_pvw_*` path is faster or slower under
specific conditions. It must separate:

- algorithmic shared-mask MAT/PVW batching gain;
- backend/SIMD gain;
- implementation details such as scratch reuse, output clearing, dense addmul,
  and per-lane materialization;
- non-blind-rotation overhead from extract, packing KS, and HW-reducing KS.

No Stage 8 result should be described as final 686 bootstrapping acceleration
unless it is reproduced at the complete SAB output boundary with correctness,
noise, resource, and backend context attached.

## Current Evidence Before Stage 8

Full SAB output boundary on WSL/Linux `spqlios`:

| r | process runs | reps per run | speedup mean | sample stddev | range |
|---:|---:|---:|---:|---:|---:|
| 1 | 3 | 2 | 1.022x | 0.063 | 0.975x-1.094x |
| 2 | 3 | 2 | 1.188x | 0.066 | 1.132x-1.261x |
| 4 | 3 | 2 | 1.312x | 0.014 | 1.302x-1.328x |

Correctness/noise gates before Stage 8:

- `r=2`: 50-seed target-shape sweep, `0 / 204800` PVW failures,
  `0 / 204800` scalar failures, `0 / 204800` pair failures.
- `r=4`: 10-seed target-shape sweep, `0 / 81920` PVW failures,
  `0 / 81920` scalar failures, `0 / 81920` pair failures.

Resource context:

- `r=2`: PVW key bytes `1.013617x` repeated scalar; PVW keygen `1.236x`
  repeated scalar; peak RSS comparable.
- `r=4`: PVW key bytes `1.065349x` repeated scalar; PVW keygen `1.179x`
  repeated scalar; peak RSS comparable.

Backend context:

- Primary performance platform remains WSL/Linux `spqlios`.
- Portable `FFT_LIB=ffnt` target-shape `r=2`, `reps=1` passed as backend smoke
  and produced `1.218x`, but this is not statistical performance evidence.

## Primary Endpoint

The primary endpoint for Stage 8 performance ablations is:

```text
speedup_vs_scalar_repeated
= repeated scalar full SAB output time for r independent lanes
  / one sab_pvw_bootstrap_binary(...) full SAB output time for r lanes
```

The timed boundary must include blind rotation, extract, full packing KS,
HW-reducing KS, and final TLWE outputs. Key generation remains excluded from
the timed bootstrap endpoint and is reported separately under resource metrics.

## Claim Labels

- Engineering-positive: same-backend full-output speedup is above `1.10x` for
  `r=2` or above `1.20x` for `r=4`, with all process runs passing correctness.
- Statistically insufficient: fewer than 10 process-level runs, no confidence
  interval, or only one backend/CPU mode.
- Failed ablation: PVW speedup falls below `1.00x`, correctness/noise fails, or
  resource overhead becomes unacceptable.
- Paper-ready: not available yet. Requires larger repeated campaigns, backend
  separation, confidence intervals, resource tables, and novelty/literature
  support.

## Ablation Matrix

### A1: Lane Count Scaling

Question:

Does shared-mask batching behave as predicted over `r=1/2/4`, and is `r=1` a
valid negative control?

Runs:

| variant | backend | r | reps per run | process runs | expected role |
|---|---|---:|---:|---:|---|
| negative control | spqlios | 1 | 2 | 3 | recorded; no stable MAT advantage |
| main target | spqlios | 2 | 2 | 3+ | already recorded; expand if needed |
| main target | spqlios | 4 | 2 | 3+ | already recorded; expand if needed |
| stress | spqlios | 8 | 1 | 1 smoke first | memory/key-size risk gate |

Correctness gate:

- Each process-level run must print `SAB_PVW_BENCH correctness ... Pass`.

Performance gate:

- Report mean, sample stddev, min, max, and per-lane average.
- `r=1` should not be used to claim acceleration; it is a fairness and overhead
  check.

Failure handling:

- If `r=1` shows large speedup, inspect benchmark symmetry and per-lane scalar
  comparison first.
- If `r=4` is strong but `r=2` is unstable, treat `r=4` as the primary target
  and keep `r=2` as a smaller-throughput setting.
- If `r=8` fails or exhausts memory, record the resource limit instead of
  forcing the run.

Recorded `r=1` negative-control command:

```bash
STAGE7_BENCH_OUT_DIR=repro/stage8_r_scaling_r1_reps2_runs3 \
SAB_PVW_BENCH_R=1 SAB_PVW_BENCH_REPS=2 STAGE7_BENCH_RUNS=3 \
bash scripts/run_stage7_bench_sweep.sh
```

Machine-readable tables:

- `repro/stage8_r_scaling_r1_reps2_runs3/summary.csv`
- `repro/stage8_r_scaling_summary.csv`

`r=1` result:

| backend | r | process runs | reps per run | PVW mean us | scalar mean us | speedup mean | sample stddev | range |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| spqlios | 1 | 3 | 2 | 11,574,338.833 | 11,809,581.333 | 1.022x | 0.063 | 0.975x-1.094x |

Interpretation:

- Every process-level run passed correctness.
- `r=1` does not show a stable throughput advantage; one run is below `1.0x`,
  one is near parity, and one is modestly above parity.
- This is the expected negative-control behavior and supports the interpretation
  that the stronger `r=2/4` full SAB gains come from multi-lane shared-mask
  batching rather than a generally faster PVW wrapper.

### A2: Backend/SIMD Separation

Question:

Is the observed speedup a same-backend algorithmic effect, or mostly a backend
artifact?

Runs:

| backend | role | required before claim |
|---|---|---|
| `spqlios` | primary WSL/Linux performance baseline | yes |
| `spqlios_avx512` | SIMD/backend sensitivity if CPU supports AVX512 | yes for backend separation |
| `ffnt` | portable correctness/backend smoke | smoke only |
| `spqlios` + `DFT_FMA_OPT` | same-ISA comparison against mbfhe-style AVX/FMA | useful for implementation comparison |

Gate:

- Compare ratios only within the same backend.
- Do not mix MOSFHET `spqlios_avx512` absolute times with mbfhe `spqlios-fma`
  as an algorithm claim.

Failure handling:

- If speedup exists only on one backend, report it as backend-specific.
- If all backends show the same direction but different magnitudes, separate
  algorithmic direction from backend magnitude.

Recorded AVX512 backend sensitivity commands:

```bash
STAGE7_BENCH_OUT_DIR=repro/stage8_backend_avx512_r2_reps2_runs3 \
FFT_LIB=spqlios_avx512 SAB_PVW_BENCH_R=2 SAB_PVW_BENCH_REPS=2 \
STAGE7_BENCH_RUNS=3 bash scripts/run_stage7_bench_sweep.sh

STAGE7_BENCH_OUT_DIR=repro/stage8_backend_avx512_r4_reps2_runs3 \
FFT_LIB=spqlios_avx512 SAB_PVW_BENCH_R=4 SAB_PVW_BENCH_REPS=2 \
STAGE7_BENCH_RUNS=3 bash scripts/run_stage7_bench_sweep.sh
```

Machine-readable table:

- `repro/stage8_backend_sensitivity_summary.csv`

Recorded backend sensitivity matrix:

| backend | r | runs | reps/run | PVW mean us | scalar mean us | speedup mean | sample stddev | range | role |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| spqlios | 2 | 3 | 2 | 19,266,121.667 | 22,848,639.333 | 1.188x | 0.066 | 1.132x-1.261x | primary sweep |
| spqlios | 4 | 3 | 2 | 35,402,965.167 | 46,436,548.167 | 1.312x | 0.014 | 1.302x-1.328x | primary sweep |
| spqlios_avx512 | 2 | 3 | 2 | 15,085,929.667 | 16,487,502.333 | 1.099x | 0.157 | 0.991x-1.280x | AVX512 sweep |
| spqlios_avx512 | 4 | 3 | 2 | 27,847,373.000 | 34,782,265.333 | 1.249x | 0.021 | 1.235x-1.274x | AVX512 sweep |
| ffnt | 2 | 1 | 1 | 37,360,973.000 | 45,495,270.000 | 1.218x | 0.000 | 1.218x-1.218x | portable smoke only |

Interpretation:

- AVX512 reduces absolute full-bootstrap time for both scalar repeated and PVW.
- At `r=2`, the AVX512 repeated sweep is positive on average but unstable:
  mean `1.099x`, sample stddev `0.157`, and one run below parity.
- At `r=4`, the AVX512 repeated sweep remains stable and positive:
  mean `1.249x`, sample stddev `0.021`, and all runs above `1.23x`.
- The relative AVX512 speedups are smaller than the primary `spqlios`
  speedups, especially for `r=2`. This matches the lower-level Stage 3
  observation that faster SIMD can reduce the relative MAT advantage by
  accelerating both scalar repeated and MAT/PVW paths.
- Backend separation now supports a cautious same-backend algorithmic direction:
  `r=4` is consistently positive across `spqlios` and `spqlios_avx512`; `r=2`
  is positive on `spqlios` but backend-sensitive under AVX512.
- A derived full-bootstrap gain-separation table is recorded in
  `docs/stage8_gain_separation.md` and
  `repro/stage8_full_bootstrap_gain_separation.csv`. It treats same-backend
  PVW-vs-repeated-scalar full SAB speedup as the algorithmic metric, and keeps
  backend/SIMD absolute timing gains in separate columns.

### A3: Boundary Ablation

Question:

Where does the full SAB speedup come from?

Boundaries:

| boundary | current evidence | next measurement |
|---|---|---|
| external product full-output | recorded in Stage 3 | keep as low-level anchor |
| isolated CMUX/RGSW/sparse_mul | correctness recorded in Stage 4/5 | add timing only if full SAB regresses |
| no-extract bootstrap | correctness recorded | add A/B timing to isolate blind rotation |
| full SAB output | Stage 7 benchmark recorded | primary endpoint |

Gate:

- If no-extract speedup is much larger than full-output speedup, the next
  optimization target is extract/materialization/packing KS.
- If no-extract and full-output speedups match, the current bottleneck remains
  blind rotation / sparse multiplication.

### A4: Kernel Implementation Variants

Question:

Can the MAT kernel reduce dense accumulation overhead without changing the SAB
protocol?

Variants:

- Clear-elision: initialize output from the first row, then add remaining rows.
  Implemented; see `docs/stage8_clear_elision_log.md`.
- Fused row/output addmul: load one decomposed DFT row and update all output
  components in a tight loop.
- Small-r specialization: dedicated `k=1,l=1,r=2` and `r=4` kernels.
- Streaming decomposition: decompose/DFT one row at a time to reduce scratch and
  cache pressure.
- FMA/AVX512 alignment: keep implementation comparisons at the same ISA level.

Gate:

- Each kernel variant first passes Stage 3 `r=1/2/4` kernel tests.
- Then it must pass Stage 5 small full-output API tests.
- Only after those gates can it enter Stage 6/7 full SAB tests.

Current decision:

- Clear-elision is the first implemented variant because it removes a known
  redundant DFT-output clear pass without changing the MAT selector layout,
  decomposition, key material, or SAB protocol.
- The kernel/small-API gate, target-shape PVW correctness gate, and scalar
  baseline gate pass after the change.
- Full repeated A/B performance is recorded for:
  - `r=2`: `1.269x` speedup mean, sample stddev `0.096`, range
    `1.172x-1.364x`;
  - `r=4`: `1.337x` speedup mean, sample stddev `0.012`, range
    `1.323x-1.345x`.
- Stage 6-style noise gates after the arithmetic-code change pass for the
  current engineering bar: `r=2` has a 50-seed deterministic sweep with
  `0 / 204800` PVW failures and gap range `[-0.470, 0.636]`; `r=4` has a
  10-seed deterministic sweep with `0 / 81920` PVW failures and gap range
  `[-0.541, 0.510]`.

Failure handling:

- If a kernel variant improves microbench but not full SAB, inspect conversion,
  materialization, and packing KS overhead.
- If a kernel variant changes noise/correctness, revert the variant or isolate
  the arithmetic bug before further benchmarking.

### A5: Resource and Key-Size Sensitivity

Question:

Does higher `r` or an implementation variant make key size, keygen time, or RSS
unacceptable?

Metrics:

- estimated public key bytes;
- keygen time;
- peak RSS from `/usr/bin/time -v`;
- internal `VmHWM`;
- raw log paths.

Gate:

- Every performance-positive variant needs a matching resource row.
- Resource overhead must be reported with speedup; it cannot be hidden behind
  throughput results.

## Execution Order

1. Run `r=1` full-output negative control on WSL/Linux `spqlios`. Done.
2. If `r=1` behaves as expected, run `spqlios_avx512` full-output `r=2/4`
   sweeps if CPU support and build remain stable. Done for `r=2/4` with
   `reps=2`, `runs=3`.
3. Add a no-extract timing boundary only if full-output speedup is much smaller
   than kernel/RGSW evidence suggests.
4. Choose exactly one kernel variant for implementation, starting with
   clear-elision or small-r specialization. Clear-elision is implemented and
   correctness-gated; repeated full-output A/B is recorded for `r=4`.
5. Repeat Stage 6 noise and Stage 7 performance gates for any variant that
   changes arithmetic code.
6. Record a full-bootstrap gain-separation table that separates same-backend
   algorithmic gain from backend/SIMD gain. Done in
   `docs/stage8_gain_separation.md`.

## Stage 8 Exit Criteria

Stage 8 is complete only when:

- `r=1/2/4` scaling is documented with full-output logs;
- at least one backend/SIMD sensitivity check is documented;
- one implementation-variant decision is made with evidence, even if the
  decision is not to implement it yet;
- negative and inconclusive results are preserved in `repro/`;
- the next Stage 9 novelty/literature task can distinguish engineering speedup
  from a defensible algorithmic contribution.

Exit assessment as of commit `d5a6b1b`:

| criterion | status | evidence |
|---|---|---|
| `r=1/2/4` full-output scaling | Pass | `repro/stage8_r_scaling_summary.csv`, `repro/stage8_clear_elision_bench_summary.csv` |
| Backend/SIMD sensitivity | Pass | `repro/stage8_backend_sensitivity_summary.csv` |
| Implementation variant decision | Pass | clear-elision implemented and recorded in `docs/stage8_clear_elision_log.md` |
| Negative/inconclusive preservation | Pass | `r=1` negative control and backend-sensitive `r=2` AVX512 result are retained in `repro/` |
| Algorithm/backend separation | Pass | `docs/stage8_gain_separation.md`, `repro/stage8_full_bootstrap_gain_separation.csv` |

Stage 8 is therefore complete at the engineering-evidence level. Remaining
items such as `r=4` 50+ seed expansion and stage-level noise probes are
paper-strengthening tasks, not blockers for entering Stage 9 novelty and
literature analysis.
