# MAT-RLWE SAB Research Program Snapshot

Current implemented algorithm object:

- exact full-MAT PVW/MAT-SAB, r-body shared-mask accumulator;
- scalar SAB baseline preserved;
- all experimental MAT/PVW changes remain explicit and gated.

Current best-supported statement:

- scoped complete-SAB amortized speedup under recorded conditions.

Current blocked statements:

- AVX512 theoretical optimality;
- successful AVX512 sub-decompose optimization;
- implemented compact/shared-output MAT-SAB algorithm;
- broad novelty.

Next research work must be either a proof unlock for compact/shared-output
MAT-SAB or a new dataflow preflight with complete-SAB projection.
