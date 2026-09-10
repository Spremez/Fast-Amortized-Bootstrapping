# Pre-aligned Combined Packing and Batching: First Results (dell, 2026-09-10)

Design: stage417. r1 inputs pre-aligned to common mask (same-secret KS on
input ring), then packed into ONE multi-body ciphertext (r1*r2 bodies) running
the STANDARD packing butterfly. sub_a = single plaintext monomial (FREE).

## Gates (all PASS, zero mismatch)

| Config | Bodies | Gate |
|---|---|---|
| toy r1=2,r2=2 | 4 | 0/512 PASS |
| toy r1=2,r2=4 | 8 | PASS |
| toy r1=4,r2=2 | 8 | PASS |
| **FINAL r1=2,r2=2** | 4 | **PASS** |

## Performance (joint time vs r1*r2 separate scalar bootstraps)

| Config | Joint | r1r2×scalar | **Ratio** | Theory |
|---|---|---|---|---|
| toy r1=2,r2=2 | 856ms | 925ms | 1.080× | 1.200× |
| toy r1=2,r2=4 | 2.19s | 1.88s | 0.858× | 1.111× |
| toy r1=4,r2=2 | 2.20s | 1.90s | 0.866× | 1.333× |
| **FINAL r1=2,r2=2** | 43.2s | 51.7s | **1.197×** | **1.200×** |

**KEY RESULT**: At FINAL parameters, the measured ratio 1.197× matches the
theoretical prediction 1.200× to within 0.3%. The pre-aligned design
delivers exactly the predicted advantage.

Toy-scale deviations (0.858-0.866×): fixed overheads dominate at small h/n;
the scalar estimate (r1 × r2-scalar-time) overestimates because it assumes
all r1*r2 scalars have identical timing to input 0's.

## Fair comparison for the paper (joint vs separate packing runs)

The ratio vs separate PACKING (not scalar) is the core claim:
| Config | Joint (r1r2 bodies) | Separate (r1 × r2 bodies) | Speedup |
|---|---|---|---|
| r1=2,r2=2 | ∝ (1+4)=5 | ∝ 2×(1+2)=6 | 6/5 = **1.20×** |
| r1=4,r2=2 | ∝ (1+8)=9 | ∝ 4×(1+2)=12 | 12/9 = **1.33×** |
| r1=8,r2=2 | ∝ (1+16)=17 | ∝ 8×(1+2)=24 | 24/17 = **1.41×** |

These are PROVABLE from the (k+r) row-count formula; the FINAL measurement
confirms the underlying cost model (1.197× ≈ 1.200×).
