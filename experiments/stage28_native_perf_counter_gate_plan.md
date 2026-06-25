# Stage 28 Native Perf-Counter Gate Plan

Date: 2026-06-25

## Objective

Decide whether the current machine can support a stronger MAT-AVX512
load/store and instruction-retirement attribution claim. This stage does not
introduce a new SAB optimization. It is a gate for claims that Stage 22
explicitly left blocked.

## Question

Can this environment run Linux `perf stat` counters reliably enough to support
the claim:

```text
The remaining MAT-AVX512 gap is explained by dense MAT arithmetic and
unavoidable register pressure/load-store behavior.
```

## Protocol

Run the lightweight probe first:

```bash
bash scripts/run_stage28_native_perf_counter_gate.sh
```

The script records:

- `perf` command availability;
- `perf_event_paranoid` when readable;
- CPU model and flags;
- basic `perf stat` smoke on `true`;
- optional heavy SAB benchmark under `perf` only when
  `STAGE28_RUN_BENCH=1`.

Optional heavy run:

```bash
STAGE28_RUN_BENCH=1 \
SAB_PVW_BENCH_R=4 \
SAB_PVW_BENCH_REPS=1 \
bash scripts/run_stage28_native_perf_counter_gate.sh
```

## Gates

Correctness:

- if the heavy benchmark is run, `SAB_PVW_BENCH correctness target_full` must
  pass.

Attribution:

- `perf_command=AVAILABLE`;
- basic `perf_smoke=PASS`;
- heavy benchmark counter log exists for the optimized r=4 path.

Claim rule:

- if any gate fails, MAT-AVX512 theoretical-optimality/load-store claims remain
  blocked;
- if the lightweight smoke passes but the heavy run is skipped, the status is
  `READY_FOR_BENCH`, not a completed attribution claim;
- if the heavy run passes, the output is still counter evidence only; it must
  be interpreted with Stage 22 generic-vs-specialized timings and objdump
  evidence before changing claim labels.

## Expected Current Outcome

On WSL2, `perf` is often unavailable or limited. A blocked result is useful
evidence: it proves why Stage 22 cannot be upgraded to a theoretical
load/store claim on this platform.

## Output

Default output directory:

```text
repro/stage28_native_perf_counter_gate/
```

Primary files:

```text
summary.csv
environment.log
perf_smoke.log
perf_smoke.err
```
