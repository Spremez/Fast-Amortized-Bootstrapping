# Exact Full-MAT Frontier Variant

Selected next route: audit-only `mat_ep_subdecomp` microarchitecture.

Not selected:

- compact selector integration, because Stage176/177 deny implementation and
  strong novelty claims;
- direct from_DFT scale/copy, because Stage174 was neutral;
- fulltile/bodymajor/streaming retuning, because prior gates were neutral or
  rejected;
- tail post-processing, because the residual share is too small.

Stage179 must either produce a concrete low-level mechanism with projected
complete-SAB impact or close the exact-path tuning branch.
