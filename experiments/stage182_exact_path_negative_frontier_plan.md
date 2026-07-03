# Stage182 Plan

Goal: convert Stage178-181 into a strict frontier so future work does not drift
into speculative theory or blind AVX512 retuning.

Inputs:

- Stage178 complete-SAB `T_bootstrap/r` endpoint.
- Stage180 split timing for sub-decompose, torus-to-DFT, addmul, and combined
  current exact MAT EP block.
- Stage181 default-off AVX512 sub-decompose gate.

Acceptance rule:

- A local kernel candidate is not enough.
- Promotion requires deterministic equivalence, microbench improvement,
  projected complete-SAB impact, and then repeated full-SAB `T_bootstrap/r`.

Decision: exact same-format blind tuning is closed; only new mechanism screens
may proceed.
