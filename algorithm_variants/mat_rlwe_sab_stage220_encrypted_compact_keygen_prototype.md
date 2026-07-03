# Encrypted Compact Keygen Prototype

This is an isolated keygen prototype.

Verified:

- dense public row count with random-looking nonduplicate masks;
- active row phase equals semantic payload plus noise;
- dummy row semantic payload is zero;
- production DFT roundtrip stays within tolerance;
- missing-active and nonzero-dummy negative controls fail.

Still blocked:

- security reduction;
- production repeated-SAB noise recurrence;
- compact EP integration;
- complete-SAB `T_bootstrap/r` benchmark.
