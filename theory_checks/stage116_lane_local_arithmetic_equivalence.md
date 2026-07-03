# Stage116 Lane-Local Arithmetic Equivalence

Date: 2026-07-03

The toy model uses the current dense shared-mask phase equation as the
reference. Off-lane body rows carry zero message but are still needed in
the current format to cancel shared-mask contributions. The lane-local
model changes the mask invariant, so each lane only accumulates the
shared row and its own body row.

## Results

| r | N | dense terms | lane-local terms | ratio | mismatches | drop failures |
|---:|---:|---:|---:|---:|---:|---:|
| 2 | 64 | 9 | 5 | 1.800000 | 0 | 128 |
| 2 | 256 | 9 | 5 | 1.800000 | 0 | 512 |
| 4 | 64 | 25 | 9 | 2.777778 | 0 | 253 |
| 4 | 256 | 25 | 9 | 2.777778 | 0 | 1009 |
| 6 | 64 | 49 | 13 | 3.769231 | 0 | 384 |
| 6 | 256 | 49 | 13 | 3.769231 | 0 | 1529 |
