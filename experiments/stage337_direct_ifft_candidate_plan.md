# Stage337 Direct IFFT Candidate Plan

Goal: test whether the direct torus-to-DFT lifecycle can be reduced without
changing PVW/MAT-SAB semantics.

Tasks:

- Inspect the direct DFT path and spqlios reverse-FFT call boundary.
- Build an isolated microbench/equivalence harness for the direct IFFT block.
- Test one flag-gated candidate: batch, reuse, or fuse lifecycle work only if
  the output DFT polynomials are bit-equivalent or within existing tolerance.
- If isolated microbench passes, run complete SAB A/B under `T_bootstrap/r`.

Gates:

- No SAB state-format change.
- No compact selector hot-path integration.
- Stage337 can claim only isolated lifecycle improvement until complete SAB A/B
  and noise/resource gates pass.
