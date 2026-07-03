# Stage201 Plan

Goal: test whether structured selector candidates survive simple public
distribution distinguishers before any implementation work.

Rules:

- row count, deterministic zero masks, and mask equality are public patterns;
- passing these finite public-pattern probes is not a security proof;
- dummy padding keeps dense public shape and cannot by itself prove speedup;
- no production code is allowed without semantic, noise, resource, and
  complete-SAB gates.
