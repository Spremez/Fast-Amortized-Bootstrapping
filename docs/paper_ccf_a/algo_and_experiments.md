# Scale-Quantized Amortized Bootstrapping: Complete Algorithm and Experimental Results

> Paper-grade technical content (Eurocrypt style), consolidating every verified result of this project. All timing numbers are server-measured (spz: Xeon Gold 6230R, spqlios AVX-512, `-march=native`, deterministic seed `MOSFHET_TEST_RNG_SEED=1`); every table row is backed by a committed artifact under `repro/`.

---

## 1 Preliminaries

**Torus and ciphertexts.** Let $T = \mathbb{Z}/2^{64}$. A TRLWE sample of rank $k=1$ under key $s \in R^k$, $R = \mathbb{Z}[X]/(X^N+1)$, is $(b, a) \in R_T^2$ with $b = m + e - s\cdot a$, noise $e$ subgaussian with torus deviation $\sigma$. TRGSW$_{l,B}$ encrypts $\mu$ as a $(k{+}1)\times l(k{+}1)$ matrix of TRLWE samples whose phase decodes $\mu\cdot g_j$, gadget column weights $g_j = 2^{64-jB}$ ($j$-th). The stock external product computes $\mu\cdot c$ by decomposing $c$ into $l$ base-$2^B$ digits; per product this costs 2 forward + 2 inverse FFTs, 4 pointwise products, and a $2N$-coefficient decomposition pass.

**DFT envelope contract (established experimentally, both FFT backends).** With coefficients converted as signed raw integers and spectra multiplied pointwise, the envelope returns the negacyclic convolution **mod $2^{64}$**; the fractional reconstruction is trustworthy while the true convolution stays below $\approx 2^{116}$, and per-term operand magnitudes must satisfy

$$\text{(SC)}\qquad \max_i |A_i|\cdot\max_j |B_j| \;\lesssim\; 2^{52}.$$

Violations of (SC) manifest as discrete integer-multiple leakage (§7).

**Amortized bootstrapping (the baseline).** The SAB of [CCS'25-686] bootstraps $n$ LWE slots at once: a slot array of $n$ TRLWE accumulators is driven through $(h{+}1)\rho N$ external products ($h$ = key weight, $\rho$ = gap precision), followed by extraction, full packing key-switch and HW-reducing key-switch. Parameter set SET_2_3_2048 (the paper's flagship): $n = N = 2048$, $h=39$, $\rho=7$, message precision 3 bits, $\sigma_{in}=2^{-15}$, $\sigma_{out}=2^{-50}$, ternary output key weight 512.

---

## 2 The Scale-Quantized External Product (SQ-EP)

**Definition 1 (Q-scale accumulator).** A TRLWE/PVW accumulator is kept at scale $Q = 2^q$: every coefficient of $(b, a)$ is $\mathrm{round}(v \cdot 2^q)$ for its torus value $v$, stored sign-extended in $T$; equivalently the ciphertext lives in $\mathbb{Z}/Q$ embedded in $T$.

**Definition 2 (SQ-EP).** With selector TRGSW sampled at $l = 1$, $B = q$ (message coefficient $\pm 2^{64-q}$), the SQ external product of a $Q$-scale accumulator $c$ by selector $C$ is

$$C \boxtimes c \;=\; \operatorname{round}_{2^q}\!\big(\mathrm{conv}(C, c)\bmod 2^{64}\big),\qquad \mathrm{round}_{2^q}(x) = \big(x + 2^{63-q}\big) \gg (64-q).$$

No digit decomposition of $c$ occurs: the operand enters the envelope at raw scale (§1), and the rescale above is *fused* with the CMUX recombination $o = o_1 + \mathrm{round}_{2^q}(\mathrm{conv}(C, o_2 - o_1))$ in a single coefficient pass.

**Theorem 1 (exactness of the message path).** For bit selectors $\mu \in \{0,1\}\cdot X^e$ and any $Q$-scale $c$ with $|c|_\infty \le 2^{q-1}$, the message part of SQ-EP equals $\mu\cdot c$ exactly: $(\mu\cdot 2^{64-q})\star c \gg (64-q) = \mu\, c$, since the intermediate stays below $2^{63}$ (no wrap). *(Verified: 24/24 message-equality gates, §6.)*

**Lemma 1 (noise, and the $\Delta$-suppression).** Per SQ-EP the torus deviation of the key-noise term is
$$\sigma\cdot 2^{q+3.5}\quad\text{versus the stock (}l{=}1,B{=}23\text{) }\sigma\cdot 2^{27.1},$$
i.e. a suppression factor $\Delta = Q^2/T = 2^{2q-64}$; every bit of $q$ below 23 buys **2 bits of $\sigma$-headroom**. The rescale rounding contributes $2^{-q-1}$ per product. For SET_2_3_2048 at $q=16$: accumulated over the full schedule the SQ ledger and the stock ledger both land at max phase deviation $\log_2 = 57.5$ (parity; Table 2).

---

## 3 The SQ-SAB Construction

**Parameters.** $q$ (accumulator quantization; floor $q \ge b_{prec}+10$; default 16), plus the stock SET parameters. The KS gadgets are runtime-tunable: $(l_{aut}, B_{aut})$ and $(\ell_{pack}, b_{pack})$ — required for Theorem 2.

**Algorithm 1 (KeyGen).** (i) Sparse binary input key via rejection sampling on $\rho$; (ii) ternary output key (weight 512); (iii) selector TRGSW family $\{s[i][j][b]\}_{j\le h, b<\rho}$ at $l{=}1, B{=}q$, encrypting the gap bits; (iv) automorphism KS key for $X^{-1}$ at $(l_{aut}, B_{aut})$; (v) packing and HW-reducing KS keys (stock).

**Algorithm 2 (CMUX, fused).** $o = o_1 + \mathrm{round}_{2^q}(\mathrm{conv}(\mathrm{sel},\, o_2 - o_1))$ — 2 fwd + 2 inv FFT, 4 pointwise, one fused coefficient pass. **NCMUX**: exact up-shift $\ll(64-q)$ of the operand to torus scale, stock automorphism KS (semantics and noise unchanged), round back to $Q$-scale, then Algorithm 2.

**Algorithm 3 (Blind rotation).** The stock $(h{+}1)\rho$-round butterfly over the $n$-slot array with Algorithms 2 replacing the stock CMUX/NCMUX; zero-copy ping-pong (the result buffer is threaded, not copied — removes $\approx$2.7 GB of memcpy per bootstrap).

**Algorithm 4 (Bootstrap).** Setup quantizes the test vector to $Q$-scale; blind rotation; exact lift $\ll(64-q)$ of every slot; stock extraction + packing KS + HW KS.

**Theorem 2 (hardened configuration, verified).** Under $\sigma_{out} \mathrel{+}= 15$ bits (restoring the CRYPTO'26 sparse-key margin, §4) with co-refined aut-KS gadget $(l_{aut}, B_{aut}) \in \{(2, 19), (4, 16)\}$ and $q \le 16$, SQ-SAB bootstraps correctly while the stock scheme fails: measured max phase deviation 59.3 (SQ, budget 60) versus 62.05 (stock, broken), at $+1.1\%$ runtime. The refinement is *necessary*: a bare $\sigma$-lift breaks both schemes, because each slot performs $\approx 140$ automorphism key-switches whose noise scales as $\sigma\cdot 2^{B_{aut}}$.

---

## 4 Sparse-Key Security and the Fairness Protocol

**Threat model (CRYPTO'26, ex-ePrint 2026/279).** Coefficient isometries ($X^j$ negacyclic rotations) let one BKZ preprocessing serve all rotated targets, amplifying hybrid attacks; the resulting security ceiling for a sparse key $(n, h, w, \delta)$ is tiered:
$$[\mathrm{P}]\;\; H - \log_2 n - \delta \;\ge\; [\mathrm{H}]\;\; 2\lambda \;\ge\; \text{estimator attacks},\qquad H = \log_2\binom{n}{h} + h\log_2 w,$$
with $\delta$ the rejection-sampling entropy loss. For the baseline's six published keys: the pure-combinatorial tier already places B4/B6/T4 *below* their claimed level, and the full estimator (MitM-H2) reduces the claimed 127.8–129.9 bits to **117.3–122.4 bits**.

**Fair re-parameterization.** At the flagship family the estimator-fair point is $h = 42$ ($n$ unchanged): the tiered ceiling rises by 8.4 bits, covering the estimator deficit with margin; $h=39$ anchors the pure-combinatorial tier (128.13). All headline comparisons run both schemes at *identical* $(h, \sigma)$.

**Security absorption (the SQ dividend).** Rotational loss is capped by $\log_2 n = 11$ bits at $n = 2048$; SQ's Lemma 1 budget absorbs a $\sigma$-lift of $2(23-q) = 14$ bits — i.e. the full margin — at 1.1% cost, which the stock scheme cannot do at any cost (fixed gadget base, Theorem 2).

---

## 5 The r-Lane Merge (SQ × PVW)

The SQ kernel transplants verbatim into the r-lane PVW structure (shared mask, $r$ bodies): the per-lane decomposition loops vanish, the dense $(k{+}r)\times(k{+}r)$ multiply consumes raw operand spectra, and one shared rescale serves all $r$ bodies. Verified by double message-equality gates against the stock r-lane implementation on identical keys/inputs/test vectors: $r{=}1$ — 0/16 mismatches ×2; $r{=}4$ — 0/64 mismatches ×2 (local), 24/24 on server.

---

## 6 Experimental Results (server, fairness protocol)

**Setup.** SET_2_3_2048, $q=16$, message precision 3, per-round back-to-back same-binary measurement, gates = full-slot message equality. Timing in μs per amortized bootstrap (2048 slots).

### Table 1 — Speed at equal true-128 security (vs the scalar SAB baseline)

| Configuration | rounds | median SQ/stock | speedup | gate | artifact |
|---|---|---|---|---|---|
| **h = 42 (estimator-fair)** | 9 | **0.8978** (min 0.8900, mean 0.9005) | **10.2%** | 9/9 Pass | `fair_timing_summary.csv` |
| h = 39 (combinatorial tier) | 9 (P0-a) + 1 (anchor) | 0.9025 / 0.8989 | 9.7–10.1% | Pass | `server_timing_summary.csv` |
| q = 23 reference | 3 | 0.906 | 9.4% | Pass | `server_run_q23.log` |
| local WSL (dev reference only) | 9 | 0.955 (min 0.927) | 4.5% | Pass | `v3_timing_summary.csv` |

### Table 2 — Noise (max phase deviation, $\log_2$; message budget = 60)

| Configuration | SQ | stock | verdict |
|---|---|---|---|
| fair point h=42, 9 rounds | 57.60 | 57.69 | parity |
| h=39 (server) | 57.45 | 57.43 | parity |
| q=23 | 57.79 | 57.43 | parity |
| **σ+15 (hardened, §4)** | **59.36 Pass** | **62.09 broken** | Theorem 2 verified |
| σ+15, aut-KS(2,19) (local) | 59.30 Pass | 62.04 broken | same |

### Table 3 — On the amortized r-lane backend (vs plain PVW stock; exclusive server, warmup, interleaved order, 5 rounds)

| Configuration | median SQ/stock | verdict |
|---|---|---|
| r=4, h=42 | 1.018 (range 0.999–1.026, ±1.3%) | parity (−1.8%) |
| r=1, h=42 | 0.994 | parity |
| gates | 24/24 Pass (server) + 0/16, 0/64 (local ×2) | merge correct |

Stock r-lane amortization over repeated scalar (stage355 matrix, 11/11 rows, 10 samples, 0 noise failures): **1.5152×–1.8271×** — the SQ merge preserves this at parity while adding the §4 hardening capability.

### Table 4 — Hardening cost (server)

| Configuration | time | gate |
|---|---|---|
| SQ fair point | 10.93 s | Pass |
| SQ fair point + σ15, aut-KS(4,16) | 11.06 s (**+1.1%**) | Pass; stock broken |

### Combined headline

At estimator-fair true-128 security: **SQ-SAB is 10.2% faster than the scalar baseline; on the fully amortized r-lane backend it runs at parity while being the only configuration that restores the CRYPTO'26 sparse-key margin (+15 bits σ) — at 1.1% cost.**

---

## 7 Negative Results (reported for reproducibility)

1. **Bare σ-lift fails both schemes** (KS noise $\propto \sigma 2^{B}$, ≈140 switches/slot) — co-refinement is necessary and sufficient (Theorem 2).
2. **Scale-contract violations are real:** the operator-bind leak of the (unmerged) LUT-late-binding line was finally pinned to a per-term $2^{62}$ product (SC violated by 10 bits); contract-safe $(B, L) = (25, 3)$ repairs the primary position exactly, with a discrete single-layer residue remaining — deferred to future work with the full diagnostic trail.
3. **Quarter-scale spectral prescale is algebraically impossible** ($|F||U| \approx 2^{125}$ vs 53-bit mantissa); the working rule is (SC).
4. Local (WSL) timing underestimates the SQ advantage (4.5% vs 10.2%): the server is the only benchmark of record.

---

## 8 Artifact map

Implementation `src/sab_sq.c` (+`src/sab_pvw_sq.c` for the merge), probes `src/probe_sq.c`/`src/probe_pvw_sq.c`, theory `theory_checks/stage356_sq_scale_sab_model.md` + `theory_checks/sparse_key_lambda_bounds/`, security preflight `scripts/sq_security_preflight_279.py`, fairness protocol `docs/stage356_fairness_protocol.md`, audit `docs/integration_audit_20260828.md`, all logs under `repro/stage356_sq_scale_sab/`.
