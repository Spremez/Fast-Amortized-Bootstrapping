# Stage289 Torus-to-DFT Array Model

For MAT-SAB r=4 with k=1 and l=1, each MAT external product converts
`k+r=5` torus polynomials into DFT form. The tested wrapper keeps the same five
reverse FFTs, but tries to reduce surrounding conversion/copy overhead by
feeding each row through a shared array interface.

The isolated model therefore predicts only a small possible gain: it does not
change FFT arithmetic count, and it can lose if scratch copies or cache effects
exceed saved function-call/processor-buffer overhead. A positive gate requires
same-backend repeated speedup before any full-SAB A/B.
