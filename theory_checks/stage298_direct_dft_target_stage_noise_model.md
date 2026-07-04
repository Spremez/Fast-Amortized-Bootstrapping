# Stage298 Target Stage-Noise Model

The gate compares PVW/MAT-SAB lane phases against repeated scalar SAB lane
phases at five target-size boundaries:

1. blind-rotate accumulator coefficient 0;
2. PVW extraction;
3. materialized TLWE lane;
4. packing key switching;
5. HW key switching.

For this stage the correctness condition is pairwise decoded equality between
PVW and scalar references at each boundary. It deliberately does not use the
hand-written nonbinary expected-LUT model as a pass/fail oracle.
