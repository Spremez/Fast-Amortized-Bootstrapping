# Candidate D D3 Complete Cost and Resource Projection

## Structural counts (contract-fixed arithmetic)

H = (h+1) * r_prec * N_in = 573,440 selector events for binary
SET_2_3_2048. B1 exact-dense performs (1+r)^2 ring products per
event; Candidate D performs 4g with g = 2 from the D2 closure, plus
2gr late-binding products, independent of r on the selector side.
The generic include-zero schedule adds 79,872 events; the
coeff-one fast path keeps the base count.

| variant | r | events | products/event | ring products |
|---|---:|---:|---:|---:|
| B1_exact_dense | 1 | 573440 | 4 | 2293760 |
| B1_exact_dense | 2 | 573440 | 9 | 5160960 |
| B1_exact_dense | 4 | 573440 | 25 | 14336000 |
| B1_exact_dense | 8 | 573440 | 81 | 46448640 |
| D_operator_generic | 1 | 653312 | 8 | 5226496 |
| D_operator_generic | 2 | 653312 | 8 | 5226496 |
| D_operator_generic | 4 | 653312 | 8 | 5226496 |
| D_operator_generic | 8 | 653312 | 8 | 5226496 |
| D_operator_coeff_one_fast | 1 | 573440 | 8 | 4587520 |
| D_operator_coeff_one_fast | 2 | 573440 | 8 | 4587520 |
| D_operator_coeff_one_fast | 4 | 573440 | 8 | 4587520 |
| D_operator_coeff_one_fast | 8 | 573440 | 8 | 4587520 |

## Complete Amdahl projection (measured phase shares)

Disjoint shares from stage322: selector external-product phase
57.6230%, materialization 38.0787%, other 4.2983% (1 minus the two
measured shares). Central ratios are the contract-fixed structural
ratios (EP 4g/25 = 0.32, materialization 2g/5 = 0.8); the central
late-binding share prices the mandatory rerandomization at two
sub_a-scale passes per lane from the measured stage322 sub_a cost.
The pessimistic scenario doubles the gadget length (EP 12/25),
raises materialization to 0.9, doubles automorphism work on its
measured 0.7716% share, and budgets 1.5% for late binding.

| scenario | ratio vs B1 | speedup vs B1 | status |
|---|---:|---:|---|
| central | 0.537590728323 | 1.860151128572 | PASS |
| pessimistic | 0.684997700000 | 1.459858916315 | PASS |

The pessimistic complete-SAB speedup must be at least 1.10 over B1
for Candidate D to enter encrypted implementation (design section
10); the emitted projection is a projection, not a measurement.

## Resource projection

B0a is anchored to FAB-2025/686 Table 5 (17.09 MB including
automorphism keys); B1 applies the stage332 paper-result-pack key
ratio 1.069425; Candidate D reuses the scalar selector keys (the
security map registers the existing scalar TRGSW samples) plus
rerandomization keys, and materializes 2g = 4 operator components
instead of (1+r) = 5 B1 bodies.

| variant | selector key | rerand key | state+scratch+output | status |
|---|---:|---:|---:|---|
| B0a | 17915904 | 0 | 32768+65536+16384 | REFERENCE |
| B0b | - | - | -+-+- | REQUIRED_NOT_YET_LOCAL |
| B1 | 19159716 | 0 | 81920+163840+65536 | REFERENCE |
| B2 | - | - | -+-+- | REQUIRED_NOT_YET_LOCAL |
| D | 17915904 | 65536 | 65536+131072+65536 | PASS |

The resource gate requires D key material and D memory within 2x of
B1; both hold with a wide margin because the operator channels are
r-independent while B1 scales with (1+r).
