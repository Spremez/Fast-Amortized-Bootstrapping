# Stage 28 Native Perf-Counter Gate Log

Date: 2026-06-25

## Purpose

Stage 22 left the MAT-AVX512 theoretical load/store optimality claim blocked
because the project had timing and objdump evidence, but not hardware
perf-counter evidence. Stage 28 adds a reproducible gate for that missing
evidence.

This stage does not change the SAB implementation and does not change the
promoted `sab_pvw_*` path. It only determines whether the current platform can
support stronger MAT-AVX512 attribution claims.

## Command

Run from WSL/Linux at the repository root:

```bash
bash scripts/run_stage28_native_perf_counter_gate.sh
```

Recorded output:

```text
repro/stage28_native_perf_counter_gate/summary.csv
repro/stage28_native_perf_counter_gate/environment.log
repro/stage28_native_perf_counter_gate/perf_smoke.log
```

## Result

Observed gate summary:

| probe | status | interpretation |
|---|---|---|
| environment | `RECORDED` | platform metadata captured |
| perf command | `MISSING` | Linux `perf` was not found in PATH |
| hardware counter gate | `BLOCKED` | hardware counters cannot support a MAT-AVX512 theoretical load/store claim on this run |

Environment facts:

```text
uname: Linux DESKTOP-55NU7VV 5.15.167.4-microsoft-standard-WSL2
perf_path: empty
perf_event_paranoid: 2
cpu: 11th Gen Intel(R) Core(TM) i7-11700 @ 2.50GHz
cpu flags: AVX2, FMA, AVX512F/DQ/CD/BW/VL/VBMI/VNNI, VAES, VPCLMULQDQ present
```

## Decision

Status:

```text
STAGE28_LIGHTWEIGHT_GATE_REPRODUCIBLE
NATIVE_PERF_COUNTERS_UNAVAILABLE_ON_CURRENT_PLATFORM
MAT_AVX512_THEORETICAL_LOAD_STORE_CLAIM_STILL_BLOCKED
```

Current allowed claim remains unchanged:

```text
The specialized MAT-AVX512 path is practically useful under same-backend
complete-SAB and microbench evidence.
```

Still not allowed:

```text
The MAT-AVX512 path has reached a hardware-counter-backed theoretical
load/store optimum.
```

## Next Action

To upgrade the claim, rerun Stage 28 on native Linux, or on WSL/Linux with
`perf` installed and usable:

```bash
STAGE28_RUN_BENCH=1 \
SAB_PVW_BENCH_R=4 \
SAB_PVW_BENCH_REPS=1 \
bash scripts/run_stage28_native_perf_counter_gate.sh
```

Only a passing heavy run should be interpreted with Stage 22
generic-vs-specialized timings and objdump evidence.
