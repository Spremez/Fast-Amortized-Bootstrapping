# Stage297 Resource Model

Direct DFT does not introduce a new SAB key format. Its expected resource risk
is runtime scratch/materialization, not public key size. Therefore Stage297
checks two side conditions:

1. reuse Stage293 target key/keygen/RSS fields for the PVW-SAB representation;
2. run selected-control and direct-DFT target final-output probes under the same
   backend and compare max RSS.

This is a local resource side condition. It is not native hardware-counter
attribution and does not close stage-wise noise.
