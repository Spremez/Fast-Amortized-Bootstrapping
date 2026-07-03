# Stage220 Plan

Goal: prototype encrypted compact keygen rows after the Stage219 API skeleton.

Gates:

- current MOSFHET static library builds;
- generated C probe compiles and runs;
- encrypted row phase equals semantic payload plus modeled noise;
- dummy rows preserve semantic-zero payload while retaining public randomness;
- DFT conversion remains within tolerance;
- skipping active rows and nonzero dummy semantics fail as negative controls;
- no SAB hot-path code is authorized.
