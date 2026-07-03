# Stage155 Experiment Plan

Goal: close the post-Stage154 local frontier using existing measured evidence,
then select a concrete Stage156 route.

Inputs:

- `repro/stage153_dual_sub_fullsab_gate/dual_sub_h14_r6_profile/run.log` for r=6 H14 body-profile attribution.
- `repro/stage148_h14_r6_repeated_refresh/summary.csv` for repeated H14 current-head evidence.
- `repro/stage151_h14_r6_fulltile_backend_smoke/summary.csv` for fulltile smoke status.
- `repro/stage153_dual_sub_fullsab_gate/summary.csv` for dual-sub full-SAB status.
- `repro/stage154_bodymajor_fullsab_closeout/summary.csv` for bodymajor full-SAB status.

Correctness gate:

- schedule counts must match the expected SAB counts.
- all referenced full-SAB candidate gates must preserve target correctness.

Performance gate:

- promote no same-format local branch unless it has full-SAB `T_bootstrap/r`
  evidence or a new count-reducing mechanism.

Failure handling:

- schedule mismatch blocks optimization.
- negative/neutral local branches are preserved as ablations and not rerun
  without a new profile-backed mechanism.
