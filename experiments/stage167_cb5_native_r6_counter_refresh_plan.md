# Stage167 Validation Plan

Goal: refresh native hardware-counter evidence for the current r=6
post-fusion PVW/MAT-SAB path on CB5.

Procedure:

1. sync current `git archive HEAD` to the remote `spz` directory;
2. build the explicit r=6 path with `spqlios_avx512`;
3. run `perf stat` on `./main`;
4. parse correctness, complete-SAB speedup, cycles, instructions, load/store,
   and AVX512 FP counters;
5. restore `perf_event_paranoid`.

The password must be supplied at runtime through `STAGE167_SSHPASS`; it must
not be written into artifacts.
