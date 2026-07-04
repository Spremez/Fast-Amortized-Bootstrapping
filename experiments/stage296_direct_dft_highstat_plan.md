# Stage296 Experiment Plan

Gates:

- 10 complete-SAB performance samples per variant;
- target correctness passes in every performance run;
- direct DFT mean `T_bootstrap/r` improves selected-control mean by at least 1.02x;
- direct DFT remains faster than repeated scalar SAB on `T_bootstrap/r`;
- 10 target final-output noise trials with zero PVW/scalar pair failures;
- CI separation is recorded as confidence evidence but not used as the only
  pass/fail boundary because local WSL timing noise can dominate tails.
