# Stage179 Plan

Goal: audit the current MAT EP/subdecomp implementation and choose whether any
exact full-MAT AVX512 code work is justified.

Rules:

- Do not implement code from combined-component timing alone.
- Do not reopen fulltile/bodymajor/streaming without a new mechanism.
- Do not touch compact SAB because Stage176/177 block it.
- The next gate must split sub_decompose, torus_to_DFT, and addmul timing.

Decision: run Stage180 split probe before code.
