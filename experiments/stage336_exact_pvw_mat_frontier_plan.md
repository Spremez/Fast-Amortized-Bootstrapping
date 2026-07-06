# Stage336 Exact PVW/MAT Frontier Plan

Goal: make implementation progress without waiting for unresolved novelty or
compact-selector blockers.

Primary endpoint: `T_bootstrap/r` for complete SAB, same backend and target
parameters as Stage331.

Tasks:

- Refresh current-head exact PVW/MAT-SAB full benchmark and MAT-EP attribution.
- Identify one closed-path optimization candidate that does not change the SAB
  state semantics: scratch reuse, active-buffer carry, direct DFT lifecycle, or
  r-specialized dense MAT addmul.
- Implement only behind a flag or internal variant.
- Run staged phase equivalence, complete SAB correctness, and repeated A/B
  timing before promotion.

Gate:

- scalar SAB default path unchanged;
- `T_bootstrap/r` is the reported metric;
- no compact selector hot-path code unless a new closed state proof exists;
- neutral and negative results are recorded.
