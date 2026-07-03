# Stage146 Variance Model

Date: 2026-07-03

The MAT-RLWE comparison endpoint is amortized `T_bootstrap/r`. A single run with a faster MAT EP does not prove a faster complete bootstrapping algorithm if run-to-run variance crosses one.

Stage146 separates three quantities:

- robust repeated evidence from Stage144;
- diagnostic body-profile attribution for MAT EP versus non-MAT work;
- promotion policy, which remains controlled by repeated complete-SAB gates.

A r4-only slow sample indicates that more kernel work is not automatically justified. The next stage must either reduce full-SAB variance, increase paired statistics, or target schedule-level work that appears in the profile.
