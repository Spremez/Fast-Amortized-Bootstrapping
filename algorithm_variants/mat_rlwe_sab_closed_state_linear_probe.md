# Closed-State Linear Probe Variant

This variant is a proof probe, not an implementation. It rejects direct public
collapse of lane-pair compact output to a standard one-mask PVW_TMLWE state.

Remaining implementation routes are not unlocked:

- keep multimask/lane-pair state and solve the generalized-input performance
  problem;
- add secret correction or key switching and prove distribution/noise;
- use dense full-MAT re-expansion, which is the current exact route;
- design a new structured equal-mask selector and prove T1/T3/T4.
