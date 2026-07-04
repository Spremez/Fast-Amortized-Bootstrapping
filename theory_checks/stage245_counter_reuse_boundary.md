# Stage245 Counter Reuse Boundary

Stage245 is a provenance and claim-boundary check, not a performance or
optimality proof.

If `main.c`, `Makefile`, `include/`, and `src/` are unchanged after Stage226,
then the Stage226 native counter run still describes the same compiled hot-path
sources under the same explicit route. This supports mechanism attribution for
the selected exact dense backend-vs-wrapper comparison.

It does not prove:

- theoretical optimality of MAT-aware AVX512;
- universal superiority of one layout;
- a new complete-SAB speedup;
- non-binary, compact-route, or all-parameter correctness.

Any future executable-code or benchmark-command change must trigger a fresh
native counter run before Stage226 counters are cited for the new binary.
