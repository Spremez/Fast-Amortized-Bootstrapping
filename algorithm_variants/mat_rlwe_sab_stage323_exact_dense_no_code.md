# Stage323 Exact Dense No-Code Route

Status: no new exact dense loop code is admitted.

Reason: the current r=4 dense MAT implementation already has the main
MAT-aware AVX load/store properties, and the explicit r4-unrolled variant was
neutral in complete SAB.

Allowed next mechanisms:

- selector-transposed key layout, only after keygen/resource/noise gates;
- structured or compact selector, only after distribution/security proof gates.

Forbidden next action: another speculative r=4 dense addmul loop rewrite
without a new counter-backed mechanism.
