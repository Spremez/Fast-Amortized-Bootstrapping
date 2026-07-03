# Stage147 H14 Route Model

Date: 2026-07-03

The r4-unrolled branch improves a local MAT EP but loses stability at complete-SAB `T_bootstrap/r`. Stage147 therefore returns to the stronger prior mechanism: reduce inverse DFT materialization/add lifetime at the backend boundary for r=6, where Stage88/89 already recorded repeated full-SAB evidence.

This is still a constant-factor implementation route, not a new asymptotic SAB algorithm. The algorithmic object remains MAT-RLWE/r-body SAB, and the endpoint remains amortized per-lane bootstrapping time.
