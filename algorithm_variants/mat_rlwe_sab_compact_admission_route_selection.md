# Compact Admission Route Selection

This is a route-selection artifact, not an implementation.

Current route decisions:

- exact full-MAT PVW/MAT-SAB: current scoped baseline;
- compact/shared-output MAT-SAB: proof-only, implementation denied;
- exact addmul dataflow: selected for Stage193 preflight;
- exact from-DFT mechanism: secondary if addmul preflight fails;
- tail setup/extract/KS: deferred.

Stage193 must not reopen rejected fulltile/bodymajor/streaming retuning unless
it identifies a genuinely new dataflow mechanism.
