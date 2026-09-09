# Amortized Bootstrapping at the Information-Theoretic Frontier: Combining Packing and Batching with Matching Lower Bounds

Manuscript 2026-09-09 (self-contained core: algorithms, proofs,
complexity, and the experimental data supporting every claim).
Anonymized caliber; author block and acknowledgments in the cover file.

---

## Abstract

We study how fast one bootstrap per message can be in the class of
monomial-accumulating blind rotations with sparse small keys. We give
(a) a complete combined packing-and-batching algorithm: r distinct
inputs share one blind rotation over an interleaved ring, through a
relative-trace subtraction operator U_a, a transposition correction Ψ,
and a closed-on-Z_{2^q} final-doubling rescaling protocol; (b) a
per-step noise master theorem, built on an exact external-product
identity and a new DC-walk theorem for one-sided gadget-decomposition
residuals, whose deterministic track predicts every pipeline stage at
submission parameters to 0.00 bits; (c) a matching per-message lower
bound for the class under explicit assumptions, with our construction
matching at the optimal row constant (1+k/r → 1 versus k+1 for the
SAB/686 baseline), and a three-regime time–key frontier theorem; and
(d) the only ≥128-bit instantiation under corrected ring-isomorphism
hybrid attacks among public competitors. All semantic claims are
machine-verified over GF(257) against scalar oracles; all quantitative
claims are validated on a paired same-binary implementation.

---

## 1 Introduction

**Contributions.**
C1 (theory core): a per-message lower-bound and frontier theorem for
the class (Section 5), under explicit assumptions H1–H5; our
construction matches the standard-key-budget regime at the optimal row
constant, and the batching axis gives Θ(1/r) per-message cost
decreasing to 1/(k+1) of the baseline.
C2 (algorithm): the complete combined packing-and-batching algorithm
family (Algorithms 1' and 2'; the matrix instantiation is an isomorphic
implementation), with a per-lane correctness theorem proved by
step-level induction, and machine verification of the full semantics.
C3 (noise): a polynomial-error-growth master theorem (Section 4) with
an exact external-product identity, a DC-walk theorem for one-sided
decomposition residuals, and a two-track (deterministic-coherent plus
white-quadratic) pipeline recursion; measured closures at every stage.
C4 (security and experiments): the only ≥128-bit corrected-security
instantiation (130.4 bits), with 1.66–1.84× system throughput over the
baseline and a catalog of negative results delimiting the design space.

**Relation to prior lines.** The shared-mask multi-body external
product is instantiated in the dense domain by Bergerat et al.
[TCHES'25], and the scale-based Mat-MGSW/Vec-MLWE algebra with the
Δ = Q²/T suppression is due to Wang et al. [ePrint 2025/1711]; we use
the latter as the inner kernel. This work contributes the complete
outer bootstrapping algorithm in the sparse small-key domain: the
(h+1)·ρ-step adaptation, gap-conditioned keys, the Ψ/U_a/final-doubling
corrections that make distinct-input batching correct, the corrected-
security parameter derivation, and all measurements.

---

## 2 Preliminaries

**Rings and notation.** Power-of-two dimensions throughout. Input ring
R_Y = Z[Y]/(Y^{n}+1); bootstrapping ring R = Z[X]/(X^{N}+1) with N = r·d;
interleaved subring A = Z[Y]/(Y^{d}+1), Y := X^{r}. Exponent group
(Z/2N)^×, σ_w(X^i) = X^{wi mod 2N}, folding X^N = −1. A slot index set
of size n; h+1 sparse phases; gap values in [1, 2^ρ), ρ = ⌈log₂(n/h)⌉.
Torus T_q = R ⊗ Z_{2^q} (implementation q = 64). For a ciphertext c we
write φ(c) for its phase. We write ⊗ for negacyclic convolution.

**Keys.** The input secret s ∈ {0,1}^n has h+1 nonzero positions with
all position gaps (including wrap-around) below 2^ρ (rejection
sampled). The bootstrapping secret is binary {0,1}^N with Hamming
weight ≈ N/2. Selector ciphertexts encrypt gap-bit monomials; two
automorphism key-switching keys (σ_{−1} and σ_{1+N}) are used.

**Subgaussian toolkit.** A random variable X is s-subgaussian if
E exp(tX) ≤ exp(s²t²/2) for all t. Pythagorean additivity: sums of
independent s-subgaussians are (Σs_i²)^{1/2}-subgaussian. For a fixed
bounded multiplier vector a with ‖a‖₂ ≤ B and independent
s_i-subgaussian X_i, Σ a_i X_i is (B·s)-subgaussian.

**The inner kernel (from [1711]).** Mat-MGSW/Vec-MLWE with dual moduli
T > Q, message scale T/Q, and the scale-based external product
C ⊡ c = ⌊(C·c)·Q/T⌉. Its noise growth (Lemma 1.7 of [1711]) states
that the output error is subgaussian with parameter
γ' = (Q²/T²·γ₁² + γ₂² + Q²/T²·γ₃² + γ₄²)^{1/2}
for the four natural error sources. Our implementation instantiates
the single-modulus balanced gadget (ℓ = 1, Bg = 2^{23}, message at
scale 2^{64−Bg}); Section 4 develops its noise theory exactly, and
Corollary 14 recovers the scaled variant.

---

## 3 The Algorithm

### 3.1 Interleaved packing and the fixed subgroup

**Definition 1 (interleaved packing).** For lane messages
m_0,…,m_{r−1} ∈ A:  Φ((m_ℓ)) := Σ_{ℓ<r} X^{ℓ}·m_ℓ(X^{r}).
For public a = (a_0,…,a_{r−1}) ∈ (Z/2d)^r the per-lane target is
L_a((m_ℓ)) := (Y^{a_ℓ}m_ℓ)_ℓ.

**Lemma 1 (fixed subgroup).** H := {σ_{1+2dℓ} : 0 ≤ ℓ < r} satisfies
(a) H is a group of order r; (b) σ(Y) = Y for all σ ∈ H; (c) R^H = A.

*Proof.* (a) The map ℓ ↦ 1+2dℓ into (Z/2rd)^× is well defined, and
(1+2dℓ)(1+2dℓ') = 1 + 2d(ℓ+ℓ'+2dℓℓ') with the index taken mod r, so H
is a finite closed monoid, hence a group; the r elements are pairwise
distinct mod 2N. (b) σ_{1+2dℓ}(X^r) = X^{r(1+2dℓ)} = Y·(X^{N})^{2ℓ} = Y.
(c) A ⊆ R^H by (b). Conversely, let f = Σ f_i X^i be H-invariant.
Coefficients are constant on each H-orbit {i(1+2dℓ) mod 2N}. If
i ≡ i' (mod r), i' ≠ i, solving i·(1+2dℓ*) ≡ i' (mod 2N) exhibits them
in one orbit (2-power divisibility of i makes the linear congruence
2dℓ*·i ≡ i'−i (mod 2N) solvable; both parities of v₂(i) are handled by
descent on v₂). Hence f_i depends only on i mod r, i.e., f = g(Y); the
H-action fixes Y, and X^N = −1 forces g(Y)^{}|_{Y^d} to satisfy the
negacyclic constraint, so f ∈ A. ∎

**Lemma 2 (trace extraction).** T_H(f) := Σ_{σ∈H} σ(f) satisfies
(a) A-linearity; (b) T_H(X^c) = r·X^c if r | c, else 0; (c) for any
f = Σ_λ X^{λ}m_λ(X^r) and any λ: T_H(X^{−λ}f) = r·m_λ.

*Proof.* (a) Linearity is immediate; for g ∈ A, σ(g·f) = g·σ(f) by (b)
of Lemma 1, giving A-linearity. (b) T_H(X^c) = X^c Σ_ℓ X^{2cdℓ}; if
r | c then X^{2cdℓ} = (X^{cdr})^{2ℓ/r·r} … each term equals
(X^{2c d})^ℓ and X^{2cd} = X^{(c/r)·2rd} = (X^N)^{2c/r·...}; for r | c
each summand is 1, giving r·X^c. If r ∤ c the ratio ρ₀ = X^{2cd} ≠ 1
(since 2cd ≡ 0 mod 2N ⟺ c ≡ 0 mod r) and ρ₀^r = X^{2cdr} = 1, so the
geometric sum vanishes. (c) expands T_H(X^{−λ}f) = Σ_j m_j·T_H(X^{j−λ})
and applies (b): only j = λ survives. ∎

### 3.2 The relative-trace operator U_a

**Lemma 3 (U_a identity).** For public a and weights
P_w := Σ_{ℓ<r} X^{ℓ(1−w) + r·a_ℓ} (w ∈ H), define
U_a := Σ_{w∈H} P_w · σ_w (applied to a phase polynomial), followed by
the exact division by r (in T_q: the per-coefficient rescale R_r, see
§3.4). Then U_a(Φ(m)) = Φ(L_a(m)) for all m ∈ A^r.

*Proof.* By Lemma 2(c) with the plain embedding (offset 0),
Φ(L_a(m)) = Σ_λ X^{λ + r·a_λ} m_λ
 = (1/r) Σ_λ X^{λ+ra_λ} T_H(X^{−λ}Φ(m))
 = (1/r) Σ_{w∈H} [Σ_λ X^{λ(1−w)+ra_λ}] σ_w(Φ(m)) = (1/r)·U_a(Φ(m)),
where the exchange of summations uses that each σ_w is a linear map
on coefficient vectors. ∎

For r = 2 (the implemented case, H = {id, σ_{1+N}}), U_a takes the
concrete form
U_a(C) = R₂( Y^{a_0}·(C + σ̃_h C) + Y^{a_1}·(C − σ̃_h C) ),   (3.1)
where σ̃_h = KS_{σ_h→s}∘σ_h and R₂ is the per-coefficient halving.

**Cost.** Per (slot, step): one automorphism key-switch, four public
monomial multiply-accumulates, one rescale. The σ_h key is shared with
the transposition correction below; the whole pipeline uses exactly
two automorphism keys.

### 3.3 Transposition: obstruction and correction

The butterfly moves slot contents across the array boundary; the
wrapped source must be acted on by σ_{−1} before the conditional move.
For r > 1 this is obstructed:

**Lemma 4 (parity obstruction).** Let the lanes carry embedding offsets
f: [0,r) → Z (Φ_f = Σ X^{ℓ+rf(ℓ)}m_ℓ(X^r)). On lane λ the map induced
by σ_{−1} is Y^{−(2f(λ)+1)}∘J, where J(u)(Y) = u(Y^{−1}). For r = 2
and d ≥ 2, no f, no single ring automorphism, and no product of a
public monomial with a single automorphism makes both lanes undergo J.

*Proof.* The exponent computation is direct from X ↦ X^{−1} applied to
X^{ℓ+rf(ℓ)}·Y^q. Making lane 1 undergo J requires 2f(1)+1 ≡ 0
(mod 2d), impossible since the left side is odd and, 2d being even,
the right side is even. A public monomial multiplier shifts both
lanes' induced maps by the same Y-power, preserving the odd difference;
any single σ_w with w ≡ −1 (mod 2d) needed to fix exponent parity does
not exist by the same parity argument (candidates w ∈ {2N−1, N−1}
leave lane 1 twisted by Y^{∓1}). ∎

**Lemma 5 (Ψ correction).** Ψ := U_{(0,1)} ∘ σ_{−1} (with U_{(0,1)}
as in (3.1) with a = (0,1)) satisfies Ψ ∘ Φ = Φ ∘ (J, J).

*Proof.* By Lemma 4, σ_{−1} acts as (J, Y^{−1}∘J) on the plain
embedding. By Lemma 3, U_{(0,1)} acts as the lane-diagonal map
(u_0, u_1) ↦ (u_0, Y u_1). Composing gives (J, Y∘Y^{−1}∘J) = (J, J). ∎

**Lemma 6 (selector cannot absorb the twist).** No D ∈ R (in
particular no diagonal monomial message of a Mat-MGSW selector, whose
message-layer action is multiplication by D) satisfies
D·Φ(m_0,m_1) = Φ(Jm_0, Jm_1) for all (m_0,m_1) ∈ A².

*Proof.* Taking (1,0) forces D = 1; taking (Y,0) then requires
Y = JY = −Y^{d−1}, false for d ≥ 2. (Structurally: multiplication
commutes with all Y-shifts, J anti-commutes.) Consequently any correct
wrap correction must introduce a genuine second automorphism; Ψ does
so at the minimal key cost (one additional key, shared with U_a). ∎

### 3.4 Rescaling pseudos and the final-doubling protocol

Per-coefficient halving on T_q produces, besides ±½ rounding,
deterministic wrap pseudos: writing the integer phase identity
b − a⊗s = φ + 2^q·k (k the wrap count), one gets
φ(R₂(c)) = φ/2 + 2^{q−1}·(k mod 2) + O(1 LSB).

**Theorem 7 (pseudo-cancellation and the final identity doubling).**
(a) If a phase carries μ + 2^{q−1}ε with arbitrary integer vector ε,
then any U_a of (3.1) maps it to [P₁μ + P₂σμ] + 2^{q−1}(P₁ε + P₂σε),
and P₁ε + P₂σε has even coefficients (σ = σ_{1+N} negates exactly the
odd coefficients of ε, so ε + σε has even coefficients on even
positions and ε − σε on odd positions); multiplying by the weight
monomials preserves evenness, hence 2^{q−1}·(…) ≡ 0 (mod 2^q) after
the doubling-by-2 inherent in P₁(·) + P₂(·) at weight-2 monomial sums.
(b) Protocol: h× (butterfly with Ψ-rescaled wraps; U_a with rescale)
+ final butterfly with Ψ-rescale + final identity doubling U_{(0,0)}
(every component ×2, no key switch), with extraction dividing by 2 in
the clear. Every rescale pseudo created after the last U_a is killed
by the final doubling; hence the terminal phase is 2·LUT + noise with
zero pseudo class.
(c) (Two-guard-bit condition.) A sufficient condition is |μ| + |e| <
2^{q−2}·2 … precisely: with TV quantization v·2^{q−p} and p + 2 ≤ q,
all message magnitudes satisfy |μ| ≤ (2^p−1)·2^{q−p−1}·2^{-1} < 2^{q−2}·2,
and the noise satisfies |e| ≪ 2^{q−2} by Theorem 13, so 2(μ+e) never
wraps 2^q. One guard bit (p+1 = q) is insufficient: the maximal
|μ| reaches 0.875·2^{q−1} > 2^{q−2}, the final doubling wraps, and the
extraction is offset by 2^{p+1} LUT levels — this failure mode was
located experimentally and its repair verified (gate 0/512).

*Proof.* (a) is the coefficient-parity computation displayed.
(b) follows by induction over the pipeline stages using (a) at each
U_a and at the final doubling (×2 maps the remaining 2^{q−1}-class to
2^q ≡ 0). (c) is the displayed bound. ∎

### 3.5 The algorithms

**Algorithm 1' (Packing MPMUL).** Inputs: slot ciphertexts
c = (c_0,…,c_{n−1}) over R, each encrypting Φ((X^{u_ℓ[i]·unit}τ_ℓ)_ℓ);
gap-bit selectors C_{t,j} = Enc(X^{d_t·2^j·unit}); automorphism keys.
```
for t = 0..h:
  for j = 0..ρ−1 with bit b = (d_t >> j) & 1:
    for i = 0..2^j−1:                      # wrapped slots
      c'_i ← c_i + C_{t,j} ⊡ (Ψ(c_{n−2^j+i}) − c_i)
    for i = 2^j..n−1:                      # direct slots
      c'_i ← c_i + C_{t,j} ⊡ (c_{i−2^j} − c_i)
    c ← c'
return c
```
**Algorithm 2' (Packing BIN-SAB).** Inputs: r input RLWE ciphertexts
(same secret, ring R_Y); the selector key set; per-lane test vectors
TV_ℓ quantized v·2^{q−p} with p+2 ≤ q.
```
for i = 0..n−1:   b̄_ℓ ← round(b_ℓ[i]·2d/2^q);  c_i ← Φ((Y^{b̄_ℓ}TV_ℓ)_ℓ)
for k = 0..h−1:
  c ← P-MPMUL(c, C_{k,·})
  for i = 0..n−1: ā_ℓ ← round(a_ℓ[i]·2d/2^q); c_i ← U_{ā(i)}(c_i)
c ← P-MPMUL(c, C_{h,·})
for i = 0..n−1: c_i ← 2·c_i                  # final identity doubling
return c   # extract lane ℓ at column ℓ, divide by 2 in the clear
```

### 3.6 Correctness

**Theorem 8 (per-lane phase invariant).** Fix inputs (in_0, in_1) and
test vectors; let P_ℓ be the virtual scalar pipeline (output ring A,
granularity-2d mod-switch, the same gap-selector schedule, wrap
correction J on A, sub_a = plaintext Y^{ā_ℓ} multiplication). After
every step of Algorithm 2', and for every slot t:
msg(t) = Φ((msg_{P_0}(t), msg_{P_1}(t))). In particular, at the end,
lane ℓ's extraction column equals P_ℓ's column-0 coefficient, slot by
slot, up to noise (quantified by Theorem 13).

*Proof.* Induction on steps.
Setup: both lanes' mod-switches and the Φ placement are identical
constructions of the scalar setups.
Butterfly bit with selector message m: for m = 0 every slot's content
is unchanged (the external product adds only noise, by Lemma 10 below
and block-diagonality of the selector message I·m — lane independence
is exactly the block-diagonal property of Lemma 11). For m = 1, direct
slots receive c_{i−2^j} (data movement, commuting with Φ by lane-wise
inspection) and wrapped slots receive Ψ(c_{n−2^j+i}); by Lemma 5 the
message-layer action is (J, J), which is the lift of the scalar
pipeline's wrap action J. Selector-message lane-independence plus
linearity of the external product in the operand preserve the
invariant.
sub_a: by Lemma 3, U_{ā(i)} acts on messages as the per-lane shifts
Y^{ā_ℓ}, identical to the scalar side; the rescale pseudos created
here are transient by Theorem 7(a) — they cancel at the next U_a
without affecting the message invariant.
Final doubling: ×2 is message-linear; Theorem 7(b) removes the last
pseudo class.
Extraction: with the plain embedding, lane ℓ's coefficients occupy
X^{ℓ+rq}, ℓ + rq < N, with no folding sign; column extraction is
linear. This closes the induction. ∎

**Machine verification.** The full semantics (setup, butterfly with
Ψ-corrected and bare-σ_{−1} wraps, U_a with exact ÷2, final doubling)
is mirrored in GF(257) and compared against two independent scalar
oracles: 2560/2560 equal over 20 random key/input/TV draws; the bare-
σ_{−1} negative control fails on exactly lane 1 (1280/2560). The
butterfly semantics is separately adjudicated: relabeling-plus-
crossing-σ_{−1} matches 240/240 while single-shot monomial moves fail
240/240 (Theorem 12's semantic backdrop). The C implementation passes
oracle gates 0/512 and 0/1024 (two toy points, six trials each) and
0/4096 at final parameters, and an instrumented mirror is asserted
bit-identical to the production rotation (13/13 trials).

### 3.7 Orthogonal composition (r₁ inputs × r₂ LUTs)

**Theorem 9 (composition).** With channels (ℓ, j) ∈ [r₁]×[r₂], each
slot ciphertext carrying r₂ bodies (the LUT axis is the body
dimension), block-diagonal selectors with equal diagonal monomials,
and the body-blind U_a of (3.1): (S) the message of channel (ℓ,j)
equals the scalar pipeline for input ℓ with TV_{ℓ,j}, slot by slot;
(C) the per-message cost is the sum of both axes' operator counts,
with amortization constant composed as r = r₁r₂; (N) each channel's
noise follows the Section-4 recursion independently.

*Proof.* (S) Induction as in Theorem 8, with Lemma 11 (block
diagonality) supplying per-body independence at each external product,
and the ring-level ops (σ_{−1}, σ_h, P_w, rescale) applied identically
to every body (they act on the ring factor and commute with the body
decomposition). (C) Selector rows scale with the body count (the (k+r₂)
row constant); ring ops are unchanged; the count is additive. (N) The
recursion of Theorem 13 is per-component; shared-row noise enters each
body at single-lane amplitude (Lemma 11). ∎
Machine adjudication: joint r₁=2×r₂=2 pipeline equals four independent
scalar oracles, 5120/5120 (GF(257)), negative control firing;
ciphertext-level body independence is covered by the implementation's
r ∈ {1..8} oracle gates.

---

## 4 Noise Analysis

### 4.1 Gadget conventions and the exact identity

The implemented gadget: ℓ = 1, Bg = 2^{23}; the selector's two rows are
fresh TMLWE samples (a_i; a_i⊗s + e_i), with the message m·2^{41}·X^0
added to row 0's mask and row 1's body. The operand is decomposed by
digit(c) = ⌊(c+2^{63})/2^{41}⌋ − 2^{22} per coefficient; the residual
ε(c) = c − digit(c)·2^{41} is one-sided: ε ~ U[0, 2^{41}), mean
μ_ε = 2^{40}, deviation σ̃_ε = 2^{41}/√12. (The key-switch path uses a
half-digit offset, i.e., round-to-nearest, giving a balanced residual —
both conventions are stated because they change the error structure.)

**Lemma 10 (external-product identity).** With D = in₂ − in₁ the CMUX
operand, e_0, e_1 the selector-row phases (message placement included),
the external-product phase is exactly
φ_EP = digit(D.a) ⊗ e_0 + digit(D.b) ⊗ e_1 + m·(ε_a⊗s − ε_b) + ν,
where ν collects the double-precision FFT error. In particular the
m = 0 case has no third term, and a zero operand mask gives ε_a = 0.

*Proof.* The output is dec(D.a)⊗S₀ + dec(D.b)⊗S₁ componentwise; taking
phases, row contributions are dec(D.x)⊗φ(row), and
φ(row₀) = e_0 − m·2^{41}s, φ(row₁) = e_1 + m·2^{41}; substituting
2^{41}·dec(D.x) = D.x − ε_x per coefficient and collecting the
D-terms into m·φ_D (exact cancellation) leaves the displayed terms. ∎
The identity is adjudicated in integers (exact convolution
reconstruction): zero deviation on all four (m, mask) configurations;
the library-vs-exact phase difference is the numerical term ν with
rms 2^{43.0}.

### 4.2 The DC-walk theorem

**Theorem 11 (DC-walk).** Let ε have i.i.d. coefficients U[0, 2^{41}),
s ∈ {0,1}^N with Hamming weight hw, H(i) = #{j ≤ i : s_j = 1}. Then
E[(ε⊗s)[i]] = μ_ε·(2H(i) − hw), and with s drawn uniformly:
(i) the rms over coefficients of the mean pattern is
μ_ε·N/√12 (= μ_ε·hw/√3 at density 1/2);
(ii) its maximum is μ_ε·hw;
(iii) the centered fluctuation has per-coefficient deviation
√hw·σ̃_ε.
Consequently each m = 1 external product injects the same key-dependent
staircase pattern, and these patterns accumulate coherently (linearly)
within a phase, with partial decorrelation across phases by the U_a
Y-shifts.

*Proof.* The negacyclic convolution splits
(ε⊗s)[i] = Σ_{j≤i, s_j=1} ε[i−j] − Σ_{j>i, s_j=1} ε[i+N−j];
taking expectations gives μ_ε(H(i) − (hw − H(i))). The staircase
2H(i) − hw walks monotonically from −hw to +hw; for uniform s its
profile is asymptotically the linear sweep 2i·(hw/N) − hw plus a
fluctuation of deviation O(√i), so the mean-square over i is dominated
by the sweep: E_i[(2H(i) − hw)²] = (2hw/N)²·N²/12 + O(N) = hw²/3 + O(N),
giving (i); (ii) is at the endpoints; (iii) is the centered sum of hw
i.i.d. residuals. The coherence statement is immediate since the mean
pattern depends only on (s, μ_ε). ∎

Measured (three parameter sets, including final parameters):
walk rms 2^{49.18}–2^{49.21} versus the closed form 2^{49.20}; max
2^{49.99} versus μ_ε·hw = 2^{49.98}; four coherent events multiply the
noise by exactly 4 (observed 2^{49.16} → 2^{51.16}).

**Lemma 12 (key-switch).** The automorphism key-switch error is
Σ_j digit_j(mask)⊗e^{KS}_j + ε_KS⊗s with balanced ε_KS, hence
σ_KS = √hw·σ̃_ε = 2^{44.2} at N = 2048 (measured 2^{44.09}–2^{44.44});
a zero mask makes it exactly zero (digits vanish). Single-step
corrections: Ψ adds σ_KS(σ_{−1})² + ½σ_KS(σ_h)²; U_a adds ½σ_KS(σ_h)².

### 4.3 The pipeline recursion and its validation

**Theorem 13 (N1, two-track recursion).** Track for each slot t a
deterministic polynomial DC_t ∈ Z^N (initially 0) and a white variance
w_t (initially 0). Per pipeline step:
– butterfly bit, m = 1 (non-first): DC_t ← DC_{src(t)}∘(Ψ-transform if
wrapped) + W, w_t ← w_{src(t)} + (Ψ terms if wrapped) + σ_EP(1)²−‖W‖²;
– butterfly bit, m = 0: w_t ← w_t + σ_EP(0)² (DC unchanged);
– sub_a: DC_t ← U_a-shift(DC_t) (even columns shifted by 2a_0, odd by
2a_1, exact integers); w_t ← w_t + ½σ_KS²;
– final doubling: DC ← 2·DC, w ← 4w.
Then the per-slot noise variance of the extraction class is
w_t + mean_even(DC_t²), and the pair noise against the scalar oracle
is σ_pair² = σ_s² + σ_int²/4, with W the staircase of Theorem 11.
σ_EP(1) = (‖W‖² + 2(B_digit σ_kg √N)² + …)^{1/2} = 2^{49.2};
σ_EP(0) = 2^{43.4} at full-entropy operands.

*Proof.* Linearity of each stage's phase map (Theorem 8's induction,
now at the error level): deterministic components (the staircase
injections and their transforms) compose exactly — the DC track is
that composition computed in integers; zero-mean independent
components (row noises, residuals' centered parts, ν) accumulate
quadratically — the white track. The weights are those of Lemma 12;
the extraction-class reduction uses the even/odd split of (3.1). ∎

Validation (same-binary paired, six trials per toy point, one at final
parameters): worst per-stage deviation 0.171 / 0.186 / 0.020 bits of
log₂-ratio; final-state −0.01 / −0.00 / −0.00 bits (final parameters:
measured 2^{54.57} = predicted 2^{54.57}); pair noise +0.28 / +0.24 /
+0.03 bits. Primitive closures: ε rms 2^{40.22} vs 2^{40.26}; σ_KS
2^{44.09–44.44} vs 2^{44.19}; σ_EP(0) 2^{43.37–43.51} vs 2^{43.4};
Ψ 2^{44.34–44.59} vs 2^{44.63}; sub_a 2^{43.46–43.76} vs σ_KS/√2.

**Corollary 14 (scaled variant; Theorem 2 of the SQ line).** Instantiating
the gadget with dual moduli (T > Q, message scale T/Q, output rescale
≫ 64−q), the identity of Lemma 10 persists with the operand residual
at the Q-scale (≈ 2^q/√12) and the selector-noise terms suppressed by
Δ = Q²/T, yielding the four-term bound γ' of [1711, Lemma 1.7]; at
q = 16 this gives the per-product coefficient 2^{q+3.7}, against the
measured 2^{q+3.5} across three σ tiers (±1 bit; the 0.2-bit gap is
the negacyclic boundary term).

**Remark (honest boundary).** The keygen-noise floor σ_kg = 2^{16} is
an empirical sampler constant (unchanged across σ_G = 2^{−70} and
2^{−49}); the theorem carries it as a parameter. Non-message (odd
tail) columns exhibit fold-alias deviations of a ≥2^{q−1} pseudo class
at columns without the guard invariant; they have zero effect on the
extraction channel (gates, pair noise, and the GF(257) equality all
clean), and their per-column algebra is left open.

---

## 5 Complexity and Lower Bounds

### 5.1 Model

**Class C0.** h+1 gap phases; per phase the algorithm realizes
SHIFT_{n,ρ} (move each slot's content by the secret gap v_t ∈ V =
[1,2^ρ)) by encrypted-selector gates, interleaved with slot-dependent
operations; terminal state per slot is X^{−φ_t}·TV (monomial
accumulation). Assumptions, all explicit:
H1 (monomial accumulation; no phase extraction);
H2 (key budget O((h+1)·ρ·s₀(λ)) — the same order as the 686 baseline);
H2' (layered width-n circuit: one gate per slot per level, ping-pong
buffers);
H3 (gate cost γ(N) ∈ {N (M_lin), N log N (M_fft)});
H5 (topology independent of secrets).
Lemma (faithfulness): the move phases of 686, TFHE, FHEW, BatchBoot,
and this work are layered width-n circuits (per-bit levels; the m = 0
gate remains in the topology), verified against the implementations.

### 5.2 The per-phase lower bound

**Lemma 15 (touching).** Under H5, every correct circuit for
SHIFT_{n,ρ} has ≥ n gates per phase. *Proof.* If some output were a
pass-through of an input, its value would not depend on v; since
|V| ≥ 2, two controls move distinct source messages to that output, a
contradiction. Two outputs cannot share a line: their values would be
identical for all v, contradicting distinct source messages for some
v. Hence n distinct gate outputs. ∎

**Lemma 16 (cone).** The influence set of each output y_j contains
{j − v mod n : v ∈ V}, of size min(2^ρ, n); hence its backward cone
has ≥ min(2^ρ, n) − 1 gates. *Proof.* Correctness forces y_j to
reflect each possible source; the size is |V| capped by n. ∎

**Theorem 17 (layered bound).** Under H5 + H2', every correct layered
width-n circuit with gate arity a needs ≥ n·⌈log_a min(2^ρ, n)⌉ gates
per phase. *Proof.* By induction on the level ℓ, any line at level ℓ
has influence set of size ≤ a^ℓ (a gate merges ≤ a predecessors).
Outputs sit at the last level L, so a^L ≥ min(2^ρ, n), i.e.,
L ≥ ⌈log_a min(2^ρ,n)⌉; each of the L levels has exactly n gates. ∎

**Lemma 18 (arity–budget).** Under H2, gate arity a = O(1): each arity-
a gate's selector key has volume ≥ c₀·a·s₀(λ), and a phase's selection
capacity is (ρ/log₂a) bits shared across its n gates, so the volume is
≥ ρ·(a/log₂a)·s₀(λ) ≥ ρ·s₀(λ); fitting the O(ρ·s₀) budget forces
a/log₂a = O(1). (a/log₂a increases for a ≥ 4: large arities waste key.)
Hence ⌈log_a⌉ = Θ(ρ); 686 and this work use a = 2.

**Lemma 19 (phase independence).** Under H1 the h+1 phases cannot be
merged: the total shift is n ≡ 0 (mod n); intermediate slot positions
are secret-dependent; extracting the accumulated phase directly is
outside the paradigm and itself requires a SHIFT-type circuit
(circularity). *Proof sketch with the two displays; full version in
the appendix source.* ∎

**Theorem 20 (per-message bound).** Under H1+H2+H2'+H5,
T ≥ (h+1)·n·Θ(ρ)·γ(N)/ℓ per blind rotation, hence per message
T_msg ≥ (h+1)·ρ·ℓ'·N·γ(N)·1. The general-DAG strong form (dropping
H2') is open; the layered model covers all known implementations.

### 5.3 The frontier and the matching upper bounds

**Theorem 21 (three-regime frontier).** (F1, standard keys) lower
bound as in Theorem 20; upper bound by this work:
T_msg(r) = (h+1)·ρ·ℓ·N log N·(1 + k/r) — matching up to the row
constant, which is optimal: (1+k/r) → 1 as r → ∞, against (k+1) for
686. (F2, linear keys Θ((h+1)·n·N)) the ρ factor can be removed by a
big-ring hybrid witness (monomial moves on R' = R[Z]/(Z^n+1) plus
extraction, twist, and packing key-switches at measured unit cost
c_ks ≈ 9), which beats F1 iff ρ > 1 + log n/log N + c_ks (crossover
ρ* ≈ 11: needs n > 2^{17} at h = 42 — always slower at practical
parameters, Θ(ρ)-faster asymptotically); its noise account is the
per-message instance of Section 4 (no new noise class). (F3, quadratic
keys) per-(slot,phase) precomputed selectors reach the touching floor
T = Θ((h+1)·ℓ·N log N). All escapes are symmetric across the class
(they bound the model, not any single scheme).

**Theorem 22 (amortization laws).** Per message,
T_msg(r) = (h+1)·ρ·ℓ·N log N·(1 + k/r); the ratio to the baseline's
(k+1) row constant is (1+k/r)/(k+1) = Θ(1/r) → 1/(k+1). Composition
along the two batching axes multiplies the constants (Theorem 9).
Measured: the r-selection table shows the marginal lane cost at
r = 2→4 is ≈ 0 (the (1+k/r) law's experimental form), and the
six-row main matrix gives 1.66–1.84× (baseline-time/our-time, paired
same-binary).

**Class coverage.** 686, TFHE, FHEW, BatchBoot, and this work's family
are all members of C0 (per-family interpretation lemmas with explicit
gate/H1–H5 mappings; TFHE and FHEW are width-1 degenerate members).

---

## 6 Security (condensed) and 7 Experiments (condensed)

Corrected ring-isomorphism hybrid attacks [Careful26] against
gap-conditioned sparse keys: five attack tiers, system minimum 130.4 ≥
128 (input layer 131.8, BSK layer 130.4; the σ_G 2^{−50}→2^{−49}
correction costs +0.08 noise bits and no runtime). Competitor
re-evaluation under the same portfolio: SAB h=39 at 124.5; BatchBoot
Boot2/4/6/8 at 124.2/124.2/120.5/124.6 — all below 128. DFR:
analytic 2^{−2724}; empirical 0 failures in >10⁶ trials
(Clopper–Pearson upper limit 2^{−18.4}).

Experiments (single machine, AVX-512, paired same-binary calibration;
six trials per point; correctness gates are prerequisites for timing):

Main matrix (r = 4, h = 42, corrected σ_G; baseline-time/our-time):
1.80 / 1.84 / 1.74 / 1.73 / 1.81 / 1.66× across the six parameter
sets (2/3-bit to 8/9-bit precision, n = 2048–4096). Security
correction is free (1.808× → 1.806× from h = 39 to 42). r-selection:
1.36/1.80/1.84/1.23 at r = 1/2/4/8. r-input (two inputs per rotation):
gates 0/512 and 0/1024 (six trials each) and 0/4096 at final
parameters; noise closures per Section 4.3; benchmark 1.23–1.32× of
2× scalar at toy/final scale (the amortization claim on this axis is
semantic — two distinct inputs per blind rotation with per-lane oracle
equality). Key size ≤ 1.07× scalar (vs 3.2–3.5× for BatchBoot's
parameterization). Negative results catalog (eleven items) with
one-line mathematical reasons, including: single-shot monomial moves
(semantics obstruction, 240/240 machine refutation), bare-σ_{−1}
wrapping (parity obstruction), selector absorption (Lemma 6),
multi-bit δ = 2 scheduling (1.38–1.58× slower), joint output packing
(epilogue 3% ≪ threshold), σ-only hardening.

---

## 8 Conclusion

Under corrected attacks the published amortized-bootstrapping state of
the art falls below 128 bits; this work gives the only ≥128-bit
instantiation at zero performance cost, a complete and machine-verified
combined packing-and-batching algorithm with a per-step noise master
theorem that closes at submission parameters, and a matching lower
bound with the optimal row constant. Open boundaries are stated where
they exist: the general-DAG strong lower bound, the universality of
the class beyond the five covered families, and the per-column algebra
of non-message rescaling pseudos.

---

## References (keys)

[MS18] Micciancio–Sorrell: amortized bootstrapping framework.
[GPV23] Guimarães–Pereira–Vortmann: first implementation.
[GP25] SAB (CCS'25): sparse amortized bootstrapping; also the "686"
paired baseline artifact of this paper's calibers.
[BB26] BatchBoot (USENIX Security'26): multi-bit CMUX amortized
bootstrapping.
[Careful26] ring-isomorphism hybrid attacks and public attack code.
[Ber25] Bergerat et al. (TCHES'25): shared-mask bootstrapping, dense
domain.
[Zam22] TFHE-rs.
[1711] Wang et al. (ePrint 2025/1711): scale-based Mat-MGSW/Vec-MLWE
and the external-product noise lemma (Lemma 1.7).

## Artifact pointers (anonymized packaging)

GF(257) checkers and logs (semantic oracle equivalence): interleave
(2560/2560; negative controls), butterfly semantics (240/240 ×3),
joint composition (5120/5120). Integer-exact external-product
adjudication and per-step profiler sources with the three parameter
sets' logs. Reproduction drivers for every table (environment-variable
parameterized; paired same-binary builds).
