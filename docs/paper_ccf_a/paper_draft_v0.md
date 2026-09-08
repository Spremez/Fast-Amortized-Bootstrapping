# Corrected-Security Sparse Amortized Bootstrapping with Shared-Mask Matrix External Products

**Working title** — 2026-09-08 draft v0.1（从 expert_delivery_document v5.1 骨架直接映射）

---

## 1 Introduction

Amortized functional bootstrapping refreshes n LWE messages in a single
pipelined invocation, reducing the per-message cost from milliseconds
(non-amortized TFHE) to microseconds. The state of the art, SAB
[Guimarães–Pereira, CCS'25], achieves this via a bit-decomposed monomial-times-
polynomial multiplication (MPmul) that runs a butterfly of CMUX/NCMUX external
products — O(h·n·log B) external products per bootstrapping with h-sparse
binary input keys and polynomial noise overhead. However, three problems
remain open:

**(P1) Security under corrected attacks.** The ring-isomorphism hybrid attacks
of CRYPTO'26 ["Careful with the Ring!"] reduce the security of sparse-key
parameters below their estimated levels. We show (§4) that the original SAB
parameters (h=39, n=2048) achieve only 124.5 bits under the corrected
portfolio — below the 128-bit target — and that the leading competitor
BatchBoot [USENIX Sec'26] has **all four of its published parameter sets**
failing (120.5–124.6 bits).

**(P2) Throughput structure.** Repeated scalar execution wastes shareable
computation. The shared-mask matrix form (one mask serving r independent LUT
evaluation lanes) eliminates this waste — but has only been instantiated in
dense GLWE domains [Bergerat et al., TCHES'25] or as a theoretical form
[Wang et al., 2025/1711]. No complete adaptation to the sparse small-key
domain exists.

**(P3) Parameter coupling.** Security correction (σ, h, KS gadget) interacts
with speed and precision domains in ways that require a closed methodology.

**Our contribution.** We construct the complete matrix sparse amortized
bootstrapping algorithm in the sparse small-key domain, using our prior work's
matrix external product as the inner kernel [Wang et al., 2025/1711], and
close all three problems:

1. **Corrected-security closure (strongest contribution).** We give a
   systematic recalibration methodology (rejection-sampling conditional-
   entropy MC + five independently computed attack tiers) and the **only
   ≥128-bit amortized bootstrapping implementation** under corrected attacks
   (min = 130.4, at +0.08 bit noise cost).

2. **Full matrix algorithm with proofs.** The outer algorithm (butterfly
   schedule + DualSubCMUX with k=2 topological optimality proof, r-lane
   multi-body structure, three secret-class variants including general sparse
   ρ-SAB, noise/precision domain management) is formalized with per-lane phase
   invariance (Prop 2.2) and machine-checked (G1' checker, 232 checks +
   negative controls). The row-product amortization law (M3, with the total-
   accounting corollary M3') gives Speedup(r) = 2r/(1+r) × Φ(r,θ) with
   six-parameter reconciliation ≤ 1.004.

3. **Measured advantage under corrected security.** On a single platform
   (dell, dual Xeon 6230R, all comparable baselines co-located):
   **1.66–1.84×** over 686 across six parameter sets (2–8 bit precision,
   n ∈ {2048, 4096}); security correction is free (h=39→42 changes speedup
   by <0.1%). Keys ≤ 1.07× of scalar (vs BatchBoot 3.2–3.5×). TFHE-rs
   same-machine anchor: 9.560 ms/PBS → full-occupancy 1.91× advantage.

4. **Honest negative results.** Three optimization candidates are formally
   closed with measured evidence: δ=2 multi-bit scheduling (correct but
   1.38–1.58× slower), joint packing (epilogue share only 3.0%), σ-only
   hardening (both SQ and standard kernels fail simultaneously).

---

## 2 Preliminaries

(TBD: LWE/RLWE/TRGSW notation; Mul-LWE/Mul-GSW ciphertext format from
1711/Bergerat; MPmul butterfly from 686; CRYPTO'26 hybrid attack model.)

## 3 The Matrix Sparse Amortized Bootstrapping Algorithm

### 3.1 Four-layer architecture

```
L1 Schedule:    686 butterfly (per-bit wrap/direct) + DualSubCMUX (k=2 optimal)
L2 Structure:   PVW_TMLWE (r bodies, shared mask) × diagonal MAT_TRGSW
L3 Kernel:      Abstract ⊡ contract — standard gadget / SQ(q) scale-quantized
                Unified family: standard ≡ SQ(q=23); selection rule q*=max(p+10, 23−m_sec/2)
L4 Engineering: 7 fusion flags (include-zero path effective: 1.5×)
```

### 3.2 Main algorithm (O1)

(Full pseudocode from `outer_algorithm_formalization.md` §3-5, with code
anchors.)

### 3.3 Correctness (Prop 2.2 / Thm 3.1)

Per-lane phase invariance by induction; oracle-verified for r=1..8, all
secret classes, all parameter sets.

### 3.4 Row-product amortization (M3 + M3')

**Theorem (M3).** [Row-work law — corrected version]

**Corollary (M3').** Speedup(r,θ) = 2r/(1+r) × Φ(r,θ), where Φ is measured
and physically attributable. Six-row reconciliation ≤ 1.004.

### 3.5 Noise (Thm 1–3 + M1/M2 upgraded)

### 3.6 G-ρ: general sparse secrets (T4)

## 4 Security Under Corrected Attacks

### 4.1 Methodology

### 4.2 Our parameters (min 130.4 ≥ 128)

### 4.3 Competitor re-evaluation (BatchBoot all FAIL)

## 5 Implementation and Experimental Results

### 5.1 Environment and fairness protocol

### 5.2 Main matrix (6 rows, r=4, corrected security)

### 5.3 r-selection benchmark

### 5.4 Precision domain and DFR

### 5.5 Competitor benchmarks (same-machine/same-binary/same-security)

### 5.6 Component profile and negative results

## 6 Related Work

## 7 Conclusion

---

*(Skeleton only — full text pending; all numbers traceable to
`expert_delivery_document.md` v5.1 single source of truth.)*
