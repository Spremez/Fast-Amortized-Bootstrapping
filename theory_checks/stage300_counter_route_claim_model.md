# Stage300 Counter Route Claim Model

Hardware counters test a mechanism claim, not the complete-SAB speed claim.
The complete-SAB endpoint remains `T_bootstrap/r`. A counter run may support
load/store/FMA attribution for a specific implementation and commit, but it
cannot be transferred from historical variants to the current direct-DFT path
without a current-head refresh.
