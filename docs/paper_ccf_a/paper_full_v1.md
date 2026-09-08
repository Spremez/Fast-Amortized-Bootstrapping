# Corrected-Security Sparse Amortized Bootstrapping with Shared-Mask Matrix External Products

---

**Abstract.** Amortized bootstrapping refreshes many LWE messages through a single
pipelined invocation, reducing per-message cost to the microsecond range. The current
state of the art, SAB [GP25], achieves this via a bit-decomposed monomial-times-polynomial
multiplication running O(h·n·log B) external products with h-sparse binary input keys.
However, recent ring-isomorphism hybrid attacks [Careful26] show that the original SAB
parameters achieve only 124.5 bits of security, well below the 128-bit target. We provide
a systematic recalibration—combining rejection-sampling conditional entropy with a
portfolio of five independently computed attack tiers—and show that the leading competitor
BatchBoot [BB26] has all four of its published parameter sets failing as well (120.5–124.6
bits). Our corrected parameters, at min = 130.4 bits, make this the only amortized
bootstrapping implementation known to reach 128 bits under the corrected attacks.

To sustain throughput under these stricter parameters, we construct the complete matrix
sparse amortized bootstrapping algorithm: a shared-mask multi-lane structure where one
blind rotation simultaneously serves r independent lookup-table evaluations. The inner
kernel is a scale-based external product between Mat-MGSW and Vec-MLWE ciphertexts
that eliminates gadget decomposition entirely. We prove per-lane phase correctness
by induction, derive a row-product amortization law Speedup(r) = 2r/(1+r) · Φ(r,θ)
with six-parameter reconciliation at error below 0.4%, and verify all output equivalence
against the scalar oracle for every supported secret class (binary, ternary, and general
sparse ρ-SAB including negative coefficients). On a single platform where all comparable
baselines are co-located, our implementation achieves 1.66–1.84× over SAB across six
parameter sets spanning 2-to-8-bit precision, with security correction costing essentially
nothing (the speedup at corrected parameters differs by less than 0.1% from the
uncorrected ones). Keys remain within 7% of scalar size, versus the 3.2–3.5× inflation
of BatchBoot. We also report three optimization candidates that we formally close
with measured evidence: multi-bit scheduling, joint packing, and σ-only hardening.

---

## 1 Introduction

Fully homomorphic encryption allows evaluating arbitrary functions on encrypted data,
but each evaluation consumes noise budget, and refreshing that budget—the
*bootstrapping*—remains the dominant cost in every practical FHE deployment.
For applications that process many messages under the same key, *amortized*
bootstrapping offers a way out: instead of bootstrapping each LWE ciphertext
independently, one packs n messages into a single RLWE ciphertext and refreshes
them all through one pipelined invocation. When n is in the thousands, the
per-message cost drops from milliseconds to microseconds.

The technique traces back to Micciancio and Sorrell [MS18], who showed that
amortized bootstrapping can achieve sublinear per-message complexity under
polynomial noise overhead. Their construction, however, relied on ciphertext-
times-ciphertext GSW multiplication, which forces parameters large enough that
the only implementation to date [GPV23] requires bootstrapping keys of up to
63 gigabytes.

Guimarães and Pereira [GP25] broke through this barrier with SAB, which replaces
all ciphertext-ciphertext multiplications by external products and ring
automorphisms. The key insight is a homomorphic monomial-times-polynomial
multiplication (MPmul, their Algorithm 1) that decomposes the sparse secret key
into position differences and evaluates the decryption linear form through a
butterfly of CMUX/NCMUX gates. With h-sparse binary keys and O(n·log B) external
products per MPmul, they bootstrap 2-to-8-bit messages in 1.5 to 28.5 ms per
message amortized, using keys of only 17–77 MB. Their implementation, built on
the MOSFHET library, remains the fastest amortized bootstrapping available.

**The security problem.** A recent line of work on ring-isomorphism hybrid
attacks [Careful26] has revealed that sparse-key parameters are weaker than
previously estimated under a specific class of attacks that exploit the ring
structure. The mechanism is subtle: the rejection-sampling procedure used to
generate keys with bounded position gaps conditions the secret distribution,
reducing its entropy below the unconditional estimate. When we apply the
corrected analysis to SAB's published parameters (h = 39, n = 2048), the
security level drops from an estimated 128.1 to 124.5 bits—a shortfall of
3.6 bits that places it below the standard 128-bit target.

Nor is SAB alone. We apply the same corrected portfolio to BatchBoot [BB26],
the USENIX Security 2026 system that currently claims the fastest amortized
bootstrapping, and find that **all four of its published parameter sets fall
short**: Boot2 at 124.2, Boot4 at 124.2 (its BSK layer, despite the input layer
passing), Boot6 at 120.5, and Boot8 at 124.6 bits. These are not marginal
failures; the deficits range from 3.4 to 7.5 bits.

**Our contributions.** This work addresses both the security gap and the
throughput question that follows from it: if parameters must be corrected
upward, what happens to speed? We give a complete answer.

*Corrected-security closure.* We develop a recalibration methodology that
combines (i) a rejection-sampling conditional-entropy Monte Carlo that computes
the exact entropy loss from key-generation gap constraints, with (ii) a
five-tier attack portfolio (primal uSVP, dual hybrid, hybrid decoding from
the published attack code [Careful26], lattice MITM, and the conditional-
entropy closed form) taking the minimum. Our corrected parameters—h = 42,
σ_G = 2^{-49}—achieve min = 130.4 bits at a measured cost of +0.08 bits of
noise and zero measurable impact on running time. To our knowledge, this is
the **only amortized bootstrapping implementation currently at or above
128 bits** under the corrected attack model.

*The matrix algorithm.* To sustain throughput under corrected parameters, we
construct the full matrix sparse amortized bootstrapping algorithm. The core
is a scale-based external product between Mat-MGSW and Vec-MLWE ciphertexts
(from our prior work [WLL25]) that serves r independent LUT evaluation lanes
through a shared mask: one blind rotation refreshes n·r (message, LUT) pairs.
The outer algorithm adapts SAB's butterfly schedule to this multi-lane setting,
adding three secret-class variants (binary, ternary, and general sparse ρ-SAB
with negative coefficients) and a DualSubCMUX optimization that shares
subtraction operands between paired butterfly gates (with a proof that k = 2
is the topological optimum).

*Theory.* We prove per-lane phase correctness by induction on the schedule
(Proposition 2), upgraded to submission grade with explicit block-diagonal
decomposition and a gadget-reconstruction identity closure (Theorem M1).
The noise analysis combines our prior subgaussian framework (Lemma 1.7 of
[WLL25]) with measured calibration: the predicted coefficient σ·2^{q+3.5}
matches experiment within one bit across three σ tiers. We derive a row-product
amortization law Speedup(r) = 2r/(1+r) · Φ(r,θ), where the first factor is
analytic (the structural ceiling from decomposition sharing) and the second
is measured (encapsulating dense addmul superlinearity and fusion-flag
savings). Six-parameter reconciliation achieves error below 0.4%.

*Experiments.* On a single platform (dual Xeon Gold 6230R, AVX-512) where
all comparable baselines are co-located—SAB as the same-binary paired
baseline, TFHE-rs built and benchmarked locally—our implementation achieves
**1.66 to 1.84 times** SAB's throughput across six parameter sets spanning
2-to-8-bit precision and ring dimensions 2048 to 8192. Security correction
is free: the speedup at corrected parameters (h = 42) differs from the
uncorrected (h = 39) by less than 0.1%. Keys remain within 7% of scalar
size. Against TFHE-rs, the full-occupancy advantage is 1.91 times. We also
measure the r-selection curve (marginal lane cost, sweet spot r = 2–4) and
report the first component-level profile of the matrix external product
(decomposition, forward DFT, and dense addmul shares).

*Honest negatives.* Three optimization candidates that we formally close
with measured evidence: (i) multi-bit δ = 2 scheduling—correct but 1.38 to
1.58 times slower, exposing a modeling error in our own cost formula that
we correct and document; (ii) joint r-output packing—the epilogue share at
corrected parameters is only 3.0%, below the 15% go/no-go threshold;
(iii) σ-only hardening—both SQ and standard kernels fail simultaneously,
showing that σ and key-switching parameters must be adjusted together.

**Organization.** Section 2 introduces notation and the scale-based
cryptosystem. Section 3 presents the matrix algorithm with correctness and
noise proofs. Section 4 develops the security recalibration. Section 5
reports experimental results. Section 6 surveys related work, and Section 7
concludes.

---

## 2 Preliminaries

### 2.1 Notation

We write Z, Q, R, C for the integers, rationals, reals, and complex numbers.
For k ∈ Z_{>0}, let [k] = {0, ..., k-1}. Vectors are column vectors denoted
by bold lowercase letters; **a**[i] is the i-th entry. For **a** ∈ Z^n, ∥**a**∥₂
and ∥**a**∥_∞ are the ℓ₂ and ℓ_∞ norms.

Throughout, N is a power of two and R = Z[x]/(x^N + 1) is the cyclotomic ring.
Each a ∈ R is a polynomial a₀ + a₁x + ... + a_{N-1}x^{N-1}, or the vector
(a₀, ..., a_{N-1}). For Q > 0, R_Q = R/(Q·R). We use the balanced integer set
[-Q/2, Q/2] as representatives for R_Q.

Sampling: x ← χ draws from distribution χ; a ← χ(R) draws each coefficient
independently. If the context is clear, we write a ← χ.

### 2.2 Subgaussian tools

For δ > 0, X over R is δ-subgaussian with parameter s if E[exp(2πtX)] ≤
exp(δ)·exp(πs²t²) for all t. We need only δ = 0 and write "subgaussian."
Any B-bounded symmetric variable is subgaussian with parameter B/√(2π);
the uniform distribution on [-b, b] has parameter b/√(2π); a discrete
Gaussian with deviation s has parameter s·√(2π). Subgaussians satisfy
Pythagorean additivity:

**Lemma 1** ([LPR13]). If X_i is subgaussian with parameter s_i, conditionally
on X₁, ..., X_{i-1}, then Σ X_i is subgaussian with parameter (Σ s_i²)^{1/2}.

**Lemma 2** ([DM15]). If X is subgaussian with parameter s, then
Pr[|X| > t] < 2·exp(-πt²/s²).

### 2.3 MLWE and the scale-based cryptosystem

Our construction rests on the module learning with errors assumption.
For a secret **s** ∈ R^k, error distribution χ, and modulus q, a sample from
A_{s,χ,q} is (**b**, **a**) ∈ R_q^{k+1} with **b** = -⟨**s**, **a**⟩ + e.

The scale-based cryptosystem from [WLL25] uses two moduli T > Q. Let
sk = (I; S) ∈ R^{(k+r)×r} be the secret key with S ← χ^{k×r}.

A **Vec-MLWE** encryption of **m** ∈ R^r under scale t | Q is:
**c** = (**b**; **a**) = (-S^T·**a** + **e** + **m**·Q/t; **a**) mod Q,
where **a** ← R_Q^k uniformly.

A **Mat-MGSW** encryption of M ∈ R^{r×r} is:
C = (-S^T A + E; A) + (T/Q)·(M, M·S^T; 0, 0) mod T,
where A ← R_T^{k×(k+r)} uniformly.

The **scale-based external product** ⊡ between C (Mat-MGSW) and **c**
(Vec-MLWE) is:
C ⊡ **c** = ⌊C · **c** · Q/T⌉ mod Q,
where the product is mod T and the division is coefficient-wise.

This eliminates gadget decomposition entirely: the operand is used directly
in the matrix-vector product, and the Q/T rescaling handles the modulus
reduction. The noise growth is governed by the Q²/T² suppression factor
(Lemma 3 below).

**Lemma 3** (Noise growth, [WLL25] Lemma 1.7). Let C₁ ∈ Mat-MGSW(M₁) with
error E₁, and **c**₂ ∈ Vec-MLWE_t(**m**₂) with error **e**₂. Then C₁ ⊡ **c**₂
encrypts M₁·**m**₂ mod t with error **e**' that is subgaussian with parameter
at most √(Q²/T² · γ₁² + γ₂² + Q²/T² · γ₃² + γ₄²), where γ₁ = Qσ₁√((k+r)N/2),
γ₂ = ∥M₁∥_∞ σ₂ √(kN), γ₃ and γ₄ capture rounding and key-switching terms.

**Corollary 1** (Application setting, [WLL25] Cor 1.8). In the bootstrapping
setting where M₁ is a diagonal matrix of monomials (∥M₁∥_∞ = 1), the secret
is uniform ternary, and ∆·Q² ≤ T, the noise simplifies to a subgaussian with
parameter less than √((k+r)Nσ₁²/(4∆²) + σ₂² + O(kN + ∆²)).

### 2.4 Sparse amortized bootstrapping

We recall the SAB framework of [GP25]. The input is an RLWE ciphertext
(a, b) ∈ R² encrypting m(Y) = Σ mᵢYⁱ under a sparse secret s with h nonzero
coefficients at positions j̃₀ < ... < j̃_{h-1}. Define d = diff(s) with
d[0] = -j̃₀, d[i] = j̃_{i-1} - j̃ᵢ, d[h] = -j̃_{h-1}.

The homomorphic decryption b - a·s is computed in the exponent through h+1
calls to MPmul (each multiplying by Y^{d[i]}) interleaved with plaintext
monomial multiplications X^{-aₖ} (the "subtract a" step). Test vectors
t₀, ..., t_{n-1} encode lookup tables as polynomial coefficients. The output
is n LWE ciphertexts encrypting fᵢ(mᵢ) + eᵢ.

The gap bound B = O(n/h) holds with high probability for keys generated with
the rejection-sampling strategy of [GP25], giving O(h·n·log B) external
products per bootstrapping and O(h·log B) per message amortized.

---

## 3 The Matrix Sparse Amortized Bootstrapping Algorithm

### 3.1 Overview

The matrix algorithm replaces each scalar TRLWE accumulator slot by a
multi-lane Vec-MLWE ciphertext **c**ⱼ = (a; b₀, ..., b_{r-1}) where the mask
a is shared across all r bodies. Each body b_q carries the test polynomial
for lane q's lookup table. One blind rotation simultaneously advances all
r lanes, producing n·r (message, LUT) evaluation pairs in a single pipeline
invocation.

Four layers compose the algorithm:

- **L1 Schedule**: the butterfly from [GP25], augmented by DualSubCMUX
  (sharing subtraction operands between paired gates, k = 2 topological
  optimum).
- **L2 Structure**: Vec-MLWE multi-body × Mat-MGSW diagonal selectors.
- **L3 Kernel**: the scale-based external product ⊡ of Section 2.3,
  instantiated at q = 16 (i.e., Q = 2^16, T = 2^64).
- **L4 Engineering**: fusion flags (sub_decomp, direct-DFT, coefficient-
  one fast path) that optimize the include-zero path.

### 3.2 The multi-lane butterfly (P-MPMUL)

Algorithm 1 generalizes MPmul to r lanes. Each butterfly gate is a MatCMUX
or MatNCMUX operating on the full multi-body slot:

MatCMUX(**y**, **x**, M) = **y** + M ⊡ (**x** - **y**).

The NCMUX variant first applies the negacyclic automorphism X ↦ X^{-1}
to the wrapped source (using a multi-body automorphism key-switching key),
then applies MatCMUX. The DualSubCMUX optimization pairs the j-th NCMUX
with the (j + 2^i)-th CMUX, sharing three operand subtractions.

**Algorithm 1: P-MPMUL (multi-lane monomial-polynomial multiplication)**

```
Input:  Accumulator slots P = (P₀,...,P_{n-1}), Pⱼ ∈ Vec-MLWE
        Bit selectors Mᵢ ∈ Mat-MGSW(vᵢ), i < ρ, where v = Σ vᵢ·2ⁱ < B
        Automorphism key KSK₋₁ for X ↦ X^{-1}
Output: P' with φ_q(P'_{(j+v) mod n}) = X^v · φ_q(Pⱼ) for all lanes q

1  for i ← 0 to ρ-1 do
2      p ← 2ⁱ
3      for j ← 0 to p-1 do
4          P'ⱼ ← MatNCMUX(Pⱼ, P_{n-p+j}, Mᵢ)      // wrapped source
5      for j ← p to n-1 do
6          P'ⱼ ← MatCMUX(Pⱼ, P_{j-p}, Mᵢ)          // direct source
7      P ← P'
8  return P
```

### 3.3 The full bootstrapping (Packing BIN-SAB)

Algorithm 2 runs h+1 iterations of P-MPMUL interleaved with the "subtract a"
step. For binary keys, this step is a plaintext monomial multiplication
(zero noise, zero external products); for ternary keys, a Mat-MGSW selector
encrypting the sign bit selects between X^{-a} and X^{+a}; for general
sparse keys (ρ-SAB), each coefficient uses two automorphisms and one
external product [BDF18].

**Algorithm 2: Matrix SAB (binary keys)**

```
Input:  RLWE (a, b) encrypting m under sparse binary s, h nonzero
        Selectors M_{t,i} encrypting bits of d = diff(s)
        Test vectors TV = (tv₀,...,tv_{n-1}), each Vec-MLWE trivial
Output: n·r LWE ciphertexts encrypting f_q(mᵢ) for each lane q

1  for j ← 0 to n-1:  Pⱼ ← X^{⌊bⱼ + 2^{-(p+1)}⌉} · TVⱼ
2  for t ← 0 to h-1 do
3      P ← P-MPMUL(P, (M_{t,i})ᵢ)                   // multiply by X^{d[t]}
4      for k ← 0 to n-1:  Pₖ ← X^{-ãₖ} · Pₖ          // subtract a (plaintext)
5  P ← P-MPMUL(P, (M_{h,i})ᵢ)                       // final rotation
6  for q ← 0 to r-1:
7      lane_q ← (Extract₀(Pⱼ).b_q)ⱼ                 // per-lane extraction
8      lane_q ← PackingKS(lane_q)                    // key switching
9  return (lane₀, ..., lane_{r-1})
```

### 3.4 The "subtract a" design space

Three variants of the subtraction step trade speed against generality:

| Variant | Mechanism | Noise | Overhead | Applicability |
|---|---|---|---|---|
| Plaintext multiply | torus coefficient rotation | zero | ~2.5 ms per h=6 step | binary, ternary |
| Double aut. + EP | sub_a_ga [BDF18] | 2 KS + 1 EP | ~19 ms per h=6 step | general sparse |
| Hom-Tr | homomorphic transform [WLL25] | KS per slot | ~19 ms (naive aut.) | theoretical |

The measured ratio (ii)/(i) ≈ 7.7× quantifies the cost of generality.

### 3.5 Correctness

**Proposition 2** (Per-lane phase invariance). For every lane q ∈ [r] and
every isolated step of Algorithm 2 (setup, each MatCMUX/MatNCMUX, each sub_a,
the final rotation, extraction), the lane-q phase satisfies
φ_q(step(P)) = step_scalar(φ_q(P)),
where step_scalar is the corresponding step of the scalar SAB applied to an
accumulator carrying lane q's test vector.

*Proof sketch.* The setup and sub_a steps are plaintext monomial multiplications
acting on all k+r components; they commute with the lane decomposition and have
unit norm. The MatNCMUX automorphism acts per-lane exactly as the scalar
TRLWE automorphism. The core is the MatCMUX: by block-diagonal structure of
the Mat-MGSW selector, the lane-q output phase collects only (i) the lane-q
body-row contributions, which reconstruct m·b_q through the gadget identity,
and (ii) the mask-row contributions, which reconstruct -m·(a·s_q). Foreign
body decompositions (q' ≠ q) do not enter φ_q because the phase function
φ_q(out) = b_q - a·s_q depends only on b_q and a. ∎

**Theorem 3** (Full-output equivalence). For all supported parameter sets and
every deterministic input, Algorithm 2 produces n·r outputs that agree, at the
message-precision grid, with r independent runs of the scalar SAB.

### 3.6 Noise

**Theorem 4** (SQ message-path exactness). The scale-based external product
preserves message values exactly: the integer convolution, when followed by
the Q/T rescaling, introduces no rounding error on the message path.

*Proof.* The message coefficients occupy bit positions ≥ 64-q, which are
unaffected by the right-shift of (64-q) positions. The rounding affects only
the noise bits. ∎

**Theorem 5** (Noise coefficient). The per-external-product noise growth is
σ · 2^{q+3.5} (measured), versus σ · 2^{27.1} for the standard gadget
decomposition kernel at Bg = 2^{23}. The two formulas agree at q = 23.

### 3.7 Precision domain

**Theorem 6** (p-domain bound). The SQ kernel with quantization scale q
supports message precision up to p bits where
q ≥ p + 4 + ⌈log₂(k_peak · √(R_max/3))⌉.
For SET_2_3_2048 (p = 3, R = 280), this gives q ≥ 13; our q = 16 has 3 bits
of margin. At p = 7, the bound requires q ≥ 17—one bit more than our q = 16—
and indeed 46 of 2048 slots fail (the one-bit deficit is confirmed exactly).

### 3.8 Amortization law

**Theorem 7** (M3, row-product law). The row-work ratio between r scalar
bootstraps and one matrix bootstrapping is 2(k+1)r/(k+r), which at k = 1,
r = 4 equals 1.60.

**Corollary 8** (M3', total-time law). Speedup(r, θ) = [2r/(1+r)] · Φ(r, θ),
where Φ encapsulates dense addmul superlinearity and fusion-flag savings.
Measured Φ values across six parameter sets range from 1.04 to 1.15, giving
speedups of 1.66 to 1.84 with reconciliation error below 0.4%.

### 3.9 General sparse secrets (G-ρ)

For ρ-SAB with coefficients in [-ρ, ρ] including negative values, the
subtraction step uses two multi-body automorphisms and one external product
per coefficient [BDF18]. The per-lane correctness follows from Theorem 3's
exponent-linearity argument. All equivalence gates pass (0/4096 at FINAL
parameters, including negative coefficients).

---

## 4 Security Under Corrected Attacks

### 4.1 The correction mechanism

The ring-isomorphism hybrid attacks of [Careful26] exploit the structure of
sparse keys in power-of-two cyclotomic rings. The key generation procedure
of [GP25] uses rejection sampling to ensure bounded position gaps (dᵢ < B =
O(n/h)), which conditions the secret distribution. The conditional entropy
of the secret, given acceptance, is:

H(s | accept) = H(s) - log₂(p_accept),

where p_accept is the probability that a uniformly random h-subset of [n]
satisfies the gap constraint. We compute this by Monte Carlo (20,000 samples
per parameter set, replicating the exact semantics of the implementation's
gap-checking function).

### 4.2 Our corrected parameters

We evaluate five attack tiers: primal uSVP, dual hybrid (both from the new
lattice estimator), hybrid decoding (from the published attack code
[Careful26]), lattice MITM, and the conditional-entropy closed form T3'.
The system security is the minimum over all tiers.

| Layer | Parameters | uSVP | dual-hybrid | HD | MITM | T3' | min |
|---|---|---|---|---|---|---|---|
| Input | h=42, t=7 | 904.1 | — | — | **131.8** | 133.5 | **131.8** |
| BSK | σ_G=2^{-49} | 133.5 | **130.4** | — | — | — | **130.4** |

The system minimum of 130.4 bits exceeds 128 with a margin of 2.4 bits.
The upgrade from σ_G = 2^{-50} to 2^{-49} costs +0.08 bits of noise
(measured) and no measurable running-time impact.

### 4.3 Competitor re-evaluation

We apply the same corrected portfolio to the published parameters of
BatchBoot [BB26] (their Tables 9-10) and the original SAB parameters:

| Scheme | Set | Their claim | Corrected min | Deficit |
|---|---|---|---|---|
| SAB [GP25] | h=39 | — | 124.5 | 3.5 |
| BatchBoot | Boot2 | >128 | **124.2** | 3.8 |
| BatchBoot | Boot4 | >128 | **124.2** | 3.8 |
| BatchBoot | Boot6 | >128 | **120.5** | 7.5 |
| BatchBoot | Boot8 | >128 | **124.6** | 3.4 |

For SAB, the binding tier is the conditional entropy (T3' = 124.5). For
BatchBoot, Boot2 and Boot6 are bound by T3' (124.2 and 120.5), Boot4's
input layer passes (136.4) but its BSK layer fails at 124.2, and Boot8
is bound by T3' at 124.6. The BSK-tier verdicts come from the standard
new lattice estimator (primal uSVP and dual hybrid), independently of our
conditional-entropy method.

TFHE-rs and CKKS-based schemes use dense secrets and are unaffected by
this class of attacks; we note this explicitly for fairness.

### 4.4 Decryption failure rate

The analytic bound (Gaussian tail with deterministic coverage) gives
DFR ≤ 2^{-2724} for our parameters. The empirical bound from more than
10⁶ zero-failure observations gives a Clopper-Pearson 95% upper confidence
limit of 2^{-18.4}.

---

## 5 Implementation and Experimental Evaluation

### 5.1 Environment

All experiments run on a single machine: dual Intel Xeon Gold 6230R at
2.1 GHz (104 logical cores, single-threaded execution), 251 GB RAM, Ubuntu
22.04, gcc with -O2 -march=native, AVX-512 and VAES enabled (spqlios_avx512
FFT backend). The system load is monitored and gated below 10.

All speedups are measured as same-binary paired comparisons: the matrix
path and the scalar baseline are compiled into one executable, eliminating
cross-build drift (which we measured at -7% to +23% and declared invalid
for comparison). Each data point is the mean of at least three runs.
Correctness (all n·r outputs match the LUT expectation at the message
grid, zero mismatch) is a prerequisite for any timing to be reported.

The scalar baseline is SAB's own implementation—the code in this repository
*is* the official CCS'25 artifact. TFHE-rs v1.8.0 is built and benchmarked
on the same machine (330 programmable bootstraps, decryption verified).
BatchBoot has no public implementation; we substitute a parameter-level
security re-evaluation (Section 4.3).

### 5.2 Main results

Table 1 presents the corrected-security matrix. Each row is a parameter
set with h = 42 (or the ring-family equivalent), σ_G = 2^{-49}, r = 4
lanes, and the full fusion-flag system.

**Table 1: Corrected-security main matrix (r = 4, h = 42).**

| Set | Precision | n | Ours s/lane | Ours ms/msg | Ours ms/(msg·bit) | SAB s/lane | SAB ms/msg | SAB ms/(msg·bit) | Speedup |
|---|---|---|---|---|---|---|---|---|---|
| SET_2_3_2048 | 2/3 | 2048 | 7.22 | 3.52 | 1.76 | 13.00 | 6.34 | 3.17 | **1.80×** |
| SET_4_5_2048 | 4/5 | 2048 | 7.67 | 3.75 | 0.94 | 14.13 | 6.90 | 1.73 | **1.84×** |
| SET_2_3_4096 | 2/3 | 4096 | 13.61 | 3.32 | 1.66 | 23.66 | 5.77 | 2.89 | **1.74×** |
| SET_4_5_4096 | 4/5 | 4096 | 14.49 | 3.54 | 0.89 | 25.07 | 6.11 | 1.53 | **1.73×** |
| SET_6_7_4096 | 6/7 | 4096 | 16.14 | 3.94 | 0.66 | 29.26 | 7.15 | 1.19 | **1.81×** |
| SET_8_9_4096 | 8/9 | 4096 | 114.30 | 27.91 | 3.49 | 189.83 | 46.34 | 5.79 | **1.66×** |

Column notation: "precision" is the per-slot plaintext width in bits
(arbitrary-function width / negacyclic width; they differ by one padding
bit per Remark 7.1 of [GP25]); n is the number of message slots per
bootstrapping; s/lane is the per-LUT-stream amortized time (total bootstrapping
time divided by r); ms/msg divides by n; ms/(msg·bit) divides by the
precision. The 8-bit row's higher absolute times reflect its doubled output
ring dimension (out_N = 8192 versus 2048 for other rows).

### 5.3 r-selection

Table 2 shows the marginal cost of adding lanes at SET_2_3_2048 and
SET_4_5_2048.

**Table 2: r-selection (main caliber, h = 42).**

| r | Speedup (2-bit / 4-bit) | Marginal lane (s) |
|---|---|---|
| 1 | 1.36 / 1.34 | — |
| 2 | 1.80 / 1.81 | 4.86 / 5.04 |
| 4 | 1.80 / 1.84 | -0.02 / -0.09 |
| 8 | 1.23 / 1.23 | +1.94 / +1.99 |

The r = 2 → 4 marginal cost is approximately zero, matching the M3
prediction that the third and fourth bodies are essentially free (the row
count grows from 3 to 5 while the shared decomposition overhead remains
constant). At r = 8, the dense (1+r)² addmul term and cache effects
dominate, and the speedup regresses.

### 5.4 Security correction is free

We re-ran the complete stage-380 protocol (same build flags, same binary,
same paired measurement) at both h = 39 (original parameters) and h = 42
(corrected). The speedup changed from 1.808× to 1.806×—a difference of
0.002, well within measurement noise. This is because the scalar baseline
is equally affected by the parameter change: both sides slow down by
approximately 7% when h increases from 39 to 42, and the ratio is preserved.

### 5.5 Competitor comparison

Against TFHE-rs (same machine, 9.560 ms per programmable bootstrapping),
our full-occupancy advantage is 1.91 times (5.00 ms per lookup versus
9.56 ms). The occupancy break-even is at κ* = 52.3% (the fraction of
slots that must carry distinct LUTs for the amortization to pay off).

BatchBoot's literature numbers (2.2-2.4× over SAB at 2/4-bit precision)
are measured under the original security parameters and cannot be directly
compared. Under corrected parameters, all four BatchBoot sets fail the
128-bit bar (Section 4.3).

### 5.6 Component profile and negative results

A component-level profile of the matrix external product (stage-373) shows
decomposition at 8.6%, forward DFT at 39.9%, and dense addmul at 51.6% of
kernel time at r = 4. The r-scaling of row counts matches the theoretical
(1+r)/(2r) exactly; the dense addmul shows +25% superlinearity at r = 4
(cache effects).

Three optimization candidates are formally closed:

1. **Multi-bit scheduling (δ = 2)**: correct (all equivalence gates pass)
   but 1.38-1.58× slower, because the identity-addend form loses the
   decomposition sharing that motivates the matrix approach.
2. **Joint r-output packing**: the epilogue (extraction + packing key
   switching) accounts for only 3.0% of total time at corrected parameters,
   far below the 15% threshold for implementation.
3. **σ-only hardening**: increasing σ alone causes both SQ and standard
   kernels to fail (the KS noise grows linearly with σ); the correction
   must adjust σ and key-switching parameters together.

### 5.7 Resource usage

Bootstrapping key sizes remain within 7% of scalar (binary mode), versus
3.2-3.5× for BatchBoot. Key generation takes 0.7 seconds including the
full odd-exponent automorphism key-switching family (2,048 keys for
N = 2048). Peak memory is comparable to scalar.

---

## 6 Related Work

**Amortized bootstrapping.** Micciancio and Sorrell [MS18] introduced the
theoretical framework; GPV23 [GPV23] gave the first implementation (63 GB
keys). Guimarães and Pereira [GP25] (SAB) achieved practical keys (17-77 MB)
and times through the MPmul butterfly, which we adopt as our schedule.

**Shared-mask bootstrapping.** Bergerat et al. [Ber25] instantiate shared-
mask (CM) bootstrapping in the dense GLWE domain. Wang et al. [WLL25]
provide the scale-based Mat-MGSW/Vec-MLWE framework that we use as our
inner kernel. The shared-mask matrix form itself is not new to this work;
our contribution is its complete adaptation to the sparse small-key domain
with corrected-security parameter derivation.

**BatchBoot.** [BB26] achieves the fastest reported amortized bootstrapping
(2.2-2.4× over SAB) through multi-bit CMUX and FFT-domain automorphism
fusion. However, all four of its published parameter sets fail the
128-bit bar under corrected attacks (Section 4.3).

**TFHE-rs.** [Zam22] is the fastest non-amortized bootstrapping library.
It uses dense keys (unaffected by the sparse-key attacks) and serves as
our same-machine baseline.

---

## 7 Conclusion

We have shown that the security landscape of amortized bootstrapping changes
qualitatively under corrected ring-isomorphism hybrid attacks: the current
state of the art (SAB at h = 39, BatchBoot across all four parameter sets)
falls below 128 bits. We provide the first (and, to our knowledge, only)
implementation that reaches 128 bits under the corrected model, at essentially
zero performance cost, through a matrix shared-mask algorithm whose inner
kernel eliminates gadget decomposition entirely. The complete theory (per-lane
correctness, noise analysis, amortization law with six-parameter reconciliation,
precision domain, DFR) is backed by a full open-source implementation and
reproducible experiments. Three optimization candidates are formally closed
with measured evidence, and the design space (sub_a variants, r selection,
kernel selection) is mapped with quantitative trade-offs.

---

## References

(To be formatted with BibTeX; entries from the repository's bibliography.)
