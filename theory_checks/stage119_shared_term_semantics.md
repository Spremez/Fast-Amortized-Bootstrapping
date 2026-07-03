# Stage119 Shared-Term Semantics

Date: 2026-07-03

Independent LUT lanes require the shared-row message to be lane-indexed.
A scalar shared term can only store one shared message and is therefore a
negative control. The viable object route is vector-shared: each lane has
a lane-local shared-row encryption and a lane-local body-row encryption.

This refines Stage117/118: the `1+2r` scalar-shared interpretation is not
valid for independent LUT lanes. The object route uses `2r` encrypted
phase terms and `4r` selector polynomials for k=1.

## Phase Rows

| r | N | variant | mismatches | negative failures | noise violations | status |
|---:|---:|---|---:|---:|---:|---|
| 2 | 64 | scalar_shared | 59 | 59 | 0 | PASS_REJECTED_SCALAR_SHARED |
| 2 | 64 | vector_shared | 0 | 0 | 0 | PASS_VECTOR_OBJECT |
| 2 | 256 | scalar_shared | 240 | 240 | 0 | PASS_REJECTED_SCALAR_SHARED |
| 2 | 256 | vector_shared | 0 | 0 | 0 | PASS_VECTOR_OBJECT |
| 4 | 64 | scalar_shared | 178 | 178 | 0 | PASS_REJECTED_SCALAR_SHARED |
| 4 | 64 | vector_shared | 0 | 0 | 0 | PASS_VECTOR_OBJECT |
| 4 | 256 | scalar_shared | 727 | 727 | 0 | PASS_REJECTED_SCALAR_SHARED |
| 4 | 256 | vector_shared | 0 | 0 | 0 | PASS_VECTOR_OBJECT |
| 6 | 64 | scalar_shared | 301 | 301 | 0 | PASS_REJECTED_SCALAR_SHARED |
| 6 | 64 | vector_shared | 0 | 0 | 0 | PASS_VECTOR_OBJECT |
| 6 | 256 | scalar_shared | 1205 | 1205 | 0 | PASS_REJECTED_SCALAR_SHARED |
| 6 | 256 | vector_shared | 0 | 0 | 0 | PASS_VECTOR_OBJECT |

## Layout Rows

| r | N | dense terms | vector terms | vector selector polys | vector/dense bytes | ratio |
|---:|---:|---:|---:|---:|---:|---:|
| 2 | 64 | 9 | 4 | 8 | 1.000000 | 2.250000 |
| 2 | 256 | 9 | 4 | 8 | 1.000000 | 2.250000 |
| 4 | 64 | 25 | 8 | 16 | 0.800000 | 3.125000 |
| 4 | 256 | 25 | 8 | 16 | 0.800000 | 3.125000 |
| 6 | 64 | 49 | 12 | 24 | 0.642857 | 4.083333 |
| 6 | 256 | 49 | 12 | 24 | 0.642857 | 4.083333 |
