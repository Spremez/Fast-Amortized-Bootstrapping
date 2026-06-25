# Stage 17 Perf Attribution Plan

Date: 2026-06-25

## Objective

Explain the Stage 16 AVX512 MAT full SAB result before making further
algorithmic changes.

Stage 17 does not introduce a new optimization. It records attribution evidence
for deciding whether Stage 18 should target:

- MAT arithmetic;
- CMUX wrapper/scratch traffic;
- RGSW monomial and sparse schedule fusion;
- backend/SIMD behavior.

## Protocol

Build the same scoped variant as Stage 16:

```text
FFT_LIB=spqlios_avx512
MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true
SAB_PVW_BENCH=true
KEY=BINARY
PARAM=SET_2_3_2048
```

Run one target full SAB benchmark for the selected r value and collect:

- benchmark stdout;
- `/usr/bin/time -v`;
- `perf stat` counters when available;
- `objdump` snippets showing AVX512 FMA instructions in `mattrgsw.o`.

## Gates

Correctness:

- `SAB_PVW_BENCH correctness target_full` must pass.

Attribution:

- if `perf` succeeds, preserve cycles/instructions/cache/branch counters;
- if `perf` fails, preserve its error and mark Stage 17 as fallback evidence;
- `objdump` must show FMA-family instructions for the MAT object.

Decision:

- no default promotion from Stage 17 alone;
- if counters are unavailable, proceed using Stage 14/16 timing and objdump
  evidence while labeling the counter evidence incomplete.

## Repro Command

```bash
STAGE17_ATTRIB_R_VALUES=4 \
STAGE17_ATTRIB_OUT_DIR=repro/stage17_perf_attribution_r4 \
bash scripts/run_stage17_perf_attribution.sh
```
