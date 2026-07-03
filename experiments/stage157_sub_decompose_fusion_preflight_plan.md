# Stage157 Experiment Plan

Goal: test whether fusing `sub = in2 - in1` with dense gadget decomposition is
worth implementing in production.

Method:

- generate a standalone C probe;
- use the dense `pvmtmlwe_decompose` offset formula;
- compare separate sub+decompose against direct decompose(in2-in1);
- benchmark target `k=1,r=6,N=2048,l=1,Bg_bit=23`.

Correctness gate: exact digit equality for every component and coefficient.

Performance gate: target fused/separate speedup must exceed the positive
threshold before production implementation.

Failure handling: if neutral or negative, keep the result as an ablation and
route to compact/cache representation work.
