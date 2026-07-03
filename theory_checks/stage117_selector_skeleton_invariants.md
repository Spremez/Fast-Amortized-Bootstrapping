# Stage117 Selector Skeleton Invariants

Date: 2026-07-03

The selector skeleton is a term map, not a ciphertext implementation. It
has one global shared term and, for each lane, one lane-local mask term
and one lane-local body term. This gives `1+2r` product terms and
`2(1+2r)` conservative selector polynomials.

| r | dense terms | skeleton terms | selector polys | acc polys | ratio |
|---:|---:|---:|---:|---:|---:|
| 2 | 9 | 5 | 10 | 4 | 1.800000 |
| 4 | 25 | 9 | 18 | 8 | 2.777778 |
| 6 | 49 | 13 | 26 | 12 | 3.769231 |
| 8 | 81 | 17 | 34 | 16 | 4.764706 |
