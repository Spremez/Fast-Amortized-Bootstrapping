# Exact Full-MAT Negative Frontier Variant

This is not a new hot-path implementation. It is the policy boundary for exact
full-MAT PVW/MAT-SAB after the AVX512 sub-decompose gate.

Rejected now:

- sub-decompose AVX512 vectorization of the same scalar formula;
- direct-scale style from_DFT retuning without a new mechanism;
- fulltile/bodymajor/streaming layout retuning without new dataflow.

Still potentially valid:

- addmul dataflow redesign with assembly/counter evidence and a projected
  complete-SAB gain;
- torus-to-DFT conversion redesign beyond Stage174;
- structured compact only after security/API/literature proof gates.
