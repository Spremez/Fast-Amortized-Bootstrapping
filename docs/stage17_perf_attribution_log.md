# Stage 17 Perf Attribution Log

Date: 2026-06-25

## Goal

Collect attribution evidence for the Stage 16 AVX512 MAT full SAB path before
starting CMUX/sparse fusion work.

Stage 17 is not a new algorithmic optimization. It answers whether the current
environment can provide hardware counters and verifies that the accepted
AVX512 MAT build actually contains FMA-family instructions.

## Commands

r=4:

```bash
STAGE17_ATTRIB_R_VALUES=4 \
STAGE17_ATTRIB_OUT_DIR=repro/stage17_perf_attribution_r4 \
bash scripts/run_stage17_perf_attribution.sh
```

r=2:

```bash
STAGE17_ATTRIB_R_VALUES=2 \
STAGE17_ATTRIB_OUT_DIR=repro/stage17_perf_attribution_r2 \
bash scripts/run_stage17_perf_attribution.sh
```

Both commands build:

```text
FFT_LIB=spqlios_avx512
MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true
SAB_PVW_BENCH=true
KEY=BINARY
PARAM=SET_2_3_2048
```

## Results

| r | correctness | perf status | PVW us | scalar repeated us | speedup | max RSS |
|---:|---|---|---:|---:|---:|---:|
| 2 | Pass | missing_fallback_time | 16,647,653 | 21,819,024 | 1.311x | 1,211,524 KB |
| 4 | Pass | missing_fallback_time | 30,571,058 | 40,786,041 | 1.334x | 2,376,336 KB |

`perf` status:

```text
perf not found
```

Therefore Stage 17 does not provide cycles, IPC, cache-miss, or branch-miss
counters. It is fallback evidence only.

Instruction audit:

```text
repro/stage17_perf_attribution_r2/r2/mattrgsw_instruction_snippet.txt
repro/stage17_perf_attribution_r4/r4/mattrgsw_instruction_snippet.txt
```

Both logs show AVX512 FMA-family instructions including:

```text
vfmadd*
vfnmadd*
vfmsub*
```

## Decision

Stage 17 supports:

```text
[objdump evidence: AVX512 FMA-family instructions present]
[fallback runtime/RSS evidence collected]
[complete target correctness still passes]
```

Stage 17 does not support:

```text
[perf-counter attribution]
[IPC/cache/bandwidth conclusion]
[default promotion]
```

The next optimization target remains the SAB body above MAT:

```text
Stage 14 already showed MAT EP is about 44%-47% of PVW body time while CMUX
is about 95%-96%. Since Stage 15/16 have brought the dense MAT AVX512 path to
a scoped positive state, additional large gains now require CMUX wrapper,
scratch, RGSW monomial, or sparse schedule fusion.
```

## Stage 18 Entry Criteria

Before editing CMUX/sparse code, Stage 18 must define:

- the exact PVW state buffers that can be reused;
- which clears/copies are semantic and which are scratch artifacts;
- lane-equivalence checks for CMUX/NCMUX and RGSW monomial;
- a profile gate showing CMUX wrapper-minus-MAT time decreases.
