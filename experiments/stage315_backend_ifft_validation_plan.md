# Stage315 Validation Plan For Stage316

1. Audit SPQLIOS reverse-transform ABI and assembly entry points.
2. Decide whether a rows=5 batch ABI can be prototyped without changing
   ciphertext semantics or key format.
3. If feasible, implement an isolated Stage316 benchmark outside SAB first.
4. Required Stage316 gate: correctness against current per-row `ifft`, plus
   >= 0.107769 isolated IFFT component reduction.
5. Only then run full SAB `T_bootstrap/r` A/B.
6. If the backend gate fails, record the negative result and move to a
   schedule-level candidate only with a concrete materialization-count proof.
