# Stage190 Plan

Goal: run an isolated T1 distribution probe for compact/shared-output selector
shortcuts.

Rules:

- do not modify `sab_pvw_*`;
- test only public distinguishers: row count, deterministic zeros, and mask
  equality relations;
- treat positive distinguishers as claim blockers, not as full security
  proofs;
- keep any new structured-key route proof-only.
