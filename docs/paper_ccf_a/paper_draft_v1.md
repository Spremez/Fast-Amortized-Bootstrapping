# Scale-Quantized Amortized Bootstrapping with Hardened Sparse Keys

## Abstract

Amortized bootstrapping (Micciancio–Sorrell, ICALP 2018; Guimarães–Pereira, CCS 2025) reduces the per-message cost of FHEW-style bootstrapping to O(h) external products, where h is the Hamming weight of the sparse secret key. We make three contributions to this framework.

First, we introduce the **scale-quantized external product**: by maintaining the blind-rotation accumulator at Q = 2^q scale and sampling selectors with gadget base q (the "squared gadget" of Wang et al., 2025), we eliminate the gadget decomposition from every external product. This yields a 10% speedup over the state-of-the-art implementation at equivalent parameters, with the noise budget decoupled as a free design parameter.

Second, we show that the coefficient-isometry hybrid attacks of Hou–Jiang–Ogilvie (CRYPTO 2026) reduce the security of all published sparse-key amortized bootstrapping parameters by 6.7–10.5 bits below their claimed 128-bit level. We derive corrected parameters and demonstrate that our scale-quantized construction absorbs the required σ-increase (15 bits) at only 1.1% additional cost — while the existing construction breaks entirely under the same hardening, because its key-switching gadget base is structurally fixed.

Third, we show that the scale-quantized kernel composes with multi-lane (PVW) batching at zero cost: the r-lane amortized throughput is preserved while gaining the hardening capability exclusively.

All experiments are conducted on a single server (Xeon Gold 6230R, AVX-512) under a fairness protocol that equalizes security across all compared configurations.

**Keywords**: amortized bootstrapping, FHE, sparse secret keys, hybrid attacks, implementation

---

## 1 Introduction

Fully homomorphic encryption (FHE) enables arbitrary computation on encrypted data, but every homomorphic operation accumulates noise. Bootstrapping — the homomorphic refresh of a ciphertext — remains the dominant cost in all FHE deployments that require unbounded computation depth.

For boolean and low-precision FHE (the FHEW/TFHE family), bootstrapping is performed via *blind rotation*: an encrypted selection polynomial is rotated by the (encrypted) LWE mask, accumulating a lookup-table evaluation. The cost is dominated by O(n) external products per bootstrapped message, where n is the LWE dimension.

**Amortized bootstrapping** (MS18; GPV23; GP25) reduces this to O(h) per message by exploiting sparse secret keys (Hamming weight h ≪ n) and batching n messages into a single blind-rotation pass. The CCS 2025 implementation (GP25, building on MOSFHET) achieves 2.5–38.7× speedups over TFHE-rs with 47.5× smaller keys.

### 1.1 Our Contributions

**Scale-quantized external product (SQ-EP).** We observe that the gadget decomposition in the external product — the step that extracts base-B digits from the accumulator — can be eliminated entirely by maintaining the accumulator at a coarser quantization Q = 2^q (Theorem 1). The selector gadget base is set to q, so the message enters at scale 2^{64-q}, and the product's message path is exact (no rounding). The key-noise term acquires a suppression factor Δ = Q²/T = 2^{2q-64} (Lemma 1): every bit of q below the stock base B = 23 buys two bits of σ-headroom. On AVX-512, this yields a 10–15% speedup (Table 1) with zero noise degradation (Table 2).

**Security hardening under CRYPTO'26 attacks.** The recent work of Hou–Jiang–Ogilvie (CRYPTO 2026) shows that coefficient isometries in power-of-two cyclotomic rings enable hybrid attacks that are strictly stronger than standard LWE estimates. For sparse-secret RLWE — exactly the regime of amortized bootstrapping — the security gap reaches 15 bits. We re-derive corrected parameters (§4) and show:

- Under σ-lifting by 15 bits, the stock construction fails (noise exceeds the message budget) because its key-switching gadget base is structurally pinned (Theorem 2).
- Our scale-quantized construction, with co-refined KS gadgets, passes at only 1.1% additional cost (Table 4). This is an asymmetric capability: no parameter adjustment can make the stock construction survive the same hardening.

**Zero-cost composition with multi-lane batching.** The PVW r-lane structure (shared-mask accumulators) amortizes the selector decomposition across r bodies. We show that SQ-EP composes with this structure at parity (Table 3): the combined configuration preserves the r-lane throughput while gaining the hardening capability exclusively.

### 1.2 Technical Overview

[Full technical overview to be written after experimental data is finalized.]

### 1.3 Paper Organization

§2: Preliminaries. §3: Scale-quantized external product. §4: Security model and fair parameter method. §5: Multi-lane composition. §6: Experiments. §7: Related work. §8: Conclusion.

---

## 2 Preliminaries

### 2.1 Notation

For a power-of-two N, let R = Z[X]/(X^N + 1) and R_T = R ⊗ Z/2^64 (the "torus"). A TRLWE sample of rank k = 1 under secret s ∈ R is (b, a) ∈ R_T² with b = m + e - s·a. A TRGSW sample with l = 1 and gadget base B encrypts μ as a 2 × 2 matrix of TRLWE samples whose gadget column carries μ·2^{64-B}.

### 2.2 Amortized bootstrapping

[Summary of the GP25 framework, blind rotation schedule, extraction, and packing.]

### 2.3 The DFT envelope

The MOSFHET DFT envelope computes the negacyclic convolution mod 2^64 of two polynomials whose coefficients are interpreted as signed integers. The fractional reconstruction is trustworthy while the true convolution stays below ≈2^116, giving the per-term scale contract:

(SC)  max|A_i| · max|B_j| ≲ 2^52.

Violations of (SC) manifest as discrete integer-multiple leakage (§7, negative results).

---

## 3 Scale-Quantized External Product

[Definitions 1–2, Theorem 1, Lemma 1, Algorithms 1–4 — see docs/paper_ccf_a/algo_and_experiments.md for the complete formal treatment.]

---

## 4 Security Model and Fair Parameter Method

[Three-tier bounds, h* table, CRYPTO'26 correction, fairness protocol — see theory_checks/sparse_key_lambda_bounds/ and docs/stage356_fairness_protocol.md.]

---

## 5 Multi-Lane Composition

[SQ-EP in the PVW r-lane structure — see stage357 results.]

---

## 6 Experiments

### 6.1 Setup

All experiments run on a single server (Intel Xeon Gold 6230R, dual-socket, AVX-512, 251 GB RAM). Both SQ and stock are compiled into the same binary with identical flags (-march=native, -O2). The fairness protocol (§4) ensures both schemes operate at the same security level.

### 6.2 Main results: per-message cost at fair security

[Table 1 from benchmark data — to be finalized with Parts 2–3 results.]

### 6.3 Noise analysis

[Table 2 — noise parity + hardening results.]

### 6.4 Multi-lane results

[Table 3 — r-lane parity + hardening.]

### 6.5 Scaling analysis

[N-trend, precision amortization, complexity model accuracy.]

---

## 7 Negative Results

We report three negative results for reproducibility:

1. **Bare σ-lifting fails both schemes** (KS noise ∝ σ·2^B, approximately 140 switches per slot).
2. **Quarter-scale spectral prescaling is algebraically impossible** (|F|·|U| ≈ 2^125 vs 53-bit mantissa).
3. **The scale contract (SC) is load-bearing**: dense multipliers violating (SC) by 10 bits produce deterministic content-scale leakage.

---

## 8 Conclusion and Future Work

[Summary + F1 (MAT-EMPmul) as projected future work.]

---

## References

[Bibliography — to be compiled.]
