# LUT-Late-Binding Operator SAB Design

Date: 2026-07-20

Status: approved conversational design; written specification pending user
review

Branch: `codex/candidate-d-lut-late-binding`

Starting commit: `ba7b2b8`

## 1. Decision And Scope

This design starts a finite research campaign for Candidate D,
LUT-Late-Binding Operator SAB.

The approved research envelope is:

- the internal accumulator and evaluation-key semantics may change;
- every cryptographic object must reduce to standard RLWE, Module-LWE, or the
  same explicitly stated GGSW circular-security assumptions already used by
  the scalar SAB baseline;
- correlated-error selectors, secret-dependent public sparsity, and
  unsupported structured distributions are not allowed;
- the external functionality remains one SAB input evaluated against `r`
  independent LUTs, producing `r` refreshed output lanes;
- scalar SAB and exact-dense PVW/MAT-SAB remain immutable baselines.

This design supersedes Candidate C as the active research direction. It does
not change or erase the terminal rejection records for Candidates A, B, or C.

## 2. Current Evidence Boundary

The repository already contains a complete exact-dense PVW/MAT-SAB path:

```text
keygen
  -> setup_tv_xb
  -> blind_rotate
  -> sparse_mul
  -> RGSW monomial butterfly
  -> CMUX/NCMUX
  -> lane extraction
  -> packing key switch
  -> final key switch
```

The current binary parameter matrix has six complete-SAB rows for `r=2` and
`r=4`. Their speedup over repeated scalar SAB ranges from `1.612100x` to
`1.747647x`, with mean `1.686741x`.

For `SET_2_3_2048`, include-zero, `r=4`, and `spqlios_avx512`:

```text
PVW/MAT complete time:          24,468,333.700 us
PVW/MAT time per lane:           6,117,083.425 us
repeated scalar total time:     42,762,012.800 us
repeated scalar time per lane:  10,690,503.200 us
speedup:                                 1.747647x
pair failures:                           0 / 10
peak RSS:                            2,415,796 KB
```

When all `N=2048` message coefficients are active, this is approximately:

```text
PVW/MAT:         2.987 ms / (lane * message coefficient)
repeated scalar: 5.220 ms / (lane * message coefficient)
```

This is a supported complete-system result. It is not evidence that the
exact-dense MAT external product is asymptotically optimal or a novel
common-mask primitive.

Candidates A, B, and C established scoped negative results:

- direct sparse standard-PVW support loses the randomization needed to hide
  the selector;
- exact factorization with inner dimension below `r` does not preserve the
  independent standard-PVW error image tested by Candidate B;
- the rank-bounded state tested by Candidate C reconstructs quadratic work or
  lacks a verified relinearization operator.

These results block another attempt to compress the same exact-PVW matrix.
They do not block changing when the LUT enters the SAB state or representing
the SAB action as a bounded operator.

## 3. Research Question

The primary research question is:

> Can the binary sparse SAB schedule be evaluated once as an encrypted,
> LUT-independent linear operator, and then bound to `r` public LUTs at the
> output, so that the encrypted hot-path cost is independent of `r` or
> subquadratic in `r`, while retaining standard RLWE/GGSW security objects,
> complete-SAB correctness, and a positive `T/(r*N_active)` result?

The intended paper-level delta is not the use of multiple LUTs itself.
Multi-output and multi-value TFHE bootstrapping are prior art. The candidate
must instead establish a SAB-specific bounded operator representation,
correctness and noise analysis, and an implementation that removes the
exact-dense `(k+r)^2` selector work from the sparse SAB hot path.

## 4. External Semantics And Primary Metric

The public operation remains:

```text
OperatorSAB(c, F_Z[0..r-1], Delta) -> out[0..r-1]
```

where:

- `c` is one RLWE ciphertext containing `N_active` active message
  coefficients;
- `F_Z[q]` is the centered, bounded, public integer LUT polynomial for lane
  `q`, with its Torus encoding fixed by the common scale `Delta`;
- `out[q]` is the refreshed result for the encoded LUT
  `TV_F[q] = Delta * F_Z[q]`.

The paper endpoint is:

```text
L(r, N_active) = T_complete_bootstrap / (r * N_active)
Throughput      = (r * N_active) / T_complete_bootstrap
```

For fixed `N_active`, `T/r` remains a useful lane-normalized proxy, but every
paper table must expose `N_active` and report the absolute per-message metric.

## 5. Binding Domain, Scale, And Operator State

Candidate D must not multiply a Torus ciphertext by a Torus-valued LUT
polynomial. Such a product is not an ordinary linear RLWE operation.

Let:

```text
R_Z = Z[X] / (X^N + 1)
R_T = T[X] / (X^N + 1)
```

For every supported LUT, define a centered, bounded integer polynomial
`F_Z in R_Z` and a common public encoding scale `Delta` such that:

```text
TV_F = Delta * F_Z in R_T
```

The supported LUT domain and the coefficient bound on `F_Z` are part of the
parameter set. Each operator channel is an ordinary Torus-RLWE ciphertext
whose noiseless phase contains the appropriately scaled operator action.
Late binding uses only addition, public automorphisms, rotations, and
multiplication by the public integer polynomial `F_Z`. Therefore it remains a
legal linear operation on Torus-RLWE ciphertexts.

If a claimed LUT family cannot be represented on one bounded integer grid, or
if the required coefficient norm destroys the decoding margin, Candidate D
must narrow its claimed LUT domain or be rejected. It may not hide a
Torus-by-Torus multiplication in `operator_state_bind`.

Candidate D represents the LUT-independent state as:

```text
U = (U_gamma) for gamma in Gamma
```

Each `U_gamma` is an ordinary RLWE ciphertext under one output secret. Masks
and errors are independently sampled across channels.

For a supported public integer LUT polynomial `F_Z`, define:

```text
L_{F_Z}(U) = sum_{gamma in Gamma} gamma(F_Z) * U_gamma
```

Let `phi_0` denote the noiseless RLWE phase. The central algebraic invariant
is:

```text
phi_0(L_{F_Z}(Update(U)))
  = phi_0(ScalarUpdate(L_{F_Z}(U))) mod R_T
```

for every supported public `F_Z` and every SAB update step. This is a
plaintext-phase equality, not byte-level or distributional ciphertext
equality. Decomposition and encryption errors are analyzed separately by the
noise gate.

The initial hypothesis for binary SAB is:

```text
Gamma = { identity, tau_minus_one }
```

This is a hypothesis, not a design assumption. The exact checker must infer
the closure generated by:

- setup rotation;
- CMUX and NCMUX;
- negacyclic wrap and sign changes;
- one complete `r_prec` RGSW monomial butterfly;
- `sub_a`; and
- the complete small-parameter sparse schedule.

Candidate D is admitted only when the inferred operator basis has
`|Gamma| <= 4`. The implementation may not add unbounded channels to avoid
this gate.

## 6. Update And Binding Interfaces

The implementation-facing internal interfaces are conceptually:

```text
operator_state_init(U, public_schedule_input)
operator_state_cmux(out, in0, in1, selector)
operator_state_ncmux(out, in0, in1, selector)
operator_state_rgsw_monomial(out, selector_bits)
operator_state_sub_a(out, public_a)
operator_state_bind(out, U, public_integer_lut, encoding_scale)
```

For ordinary CMUX, each channel is expected to follow:

```text
U'_gamma =
    U0_gamma + EP(selector, U1_gamma - U0_gamma)
```

NCMUX may permute or apply an automorphism to the operator channels before the
same scalar external product. The exact permutation is a proof obligation and
must be derived from the scalar SAB operation. It must not be inserted only
because it makes finite examples pass.

Late binding occurs after the encrypted sparse schedule:

```text
acc_q = L_{F_Z[q]}(U_final)
```

The existing extraction and key-switching tail may be reused if `acc_q`
materializes as the same scalar RLWE state expected by the baseline.

## 7. Correctness Admission Gate

Before encrypted hot-path code is written, an exact finite checker must run in:

```text
R_test = GF(257)[X] / (X^N + 1)
N in {8, 16}
```

The checker must use every polynomial basis vector `F=X^j`, not only random
LUTs. Because the update and binding maps are linear, basis-vector equality is
the finite proof obligation for arbitrary polynomials in the test ring.

For the initial supported output domains, centered coefficients must lie in
`[-128, 128]`, so reduction into `GF(257)` is injective. A larger LUT
coefficient domain requires a correspondingly larger exact field or a
Chinese-remainder checker. The finite checker establishes ideal algebraic
semantics only; it does not establish Torus scaling, decomposition error, or
the final decoding margin.

The checker must cover:

1. operator initialization;
2. selectors `mu=0` and `mu=1`;
3. all small-ring rotation offsets;
4. every negacyclic wrap boundary;
5. CMUX and NCMUX;
6. one full `r_prec` monomial butterfly;
7. `sub_a`;
8. one complete small sparse schedule; and
9. final late binding.

Mandatory negative controls are:

- remove one required operator channel;
- omit the channel permutation or swap induced by `tau_minus_one`;
- use the wrong sign on a negacyclic wrap.

All negative controls must fail. A checker that accepts an intentionally
broken construction is itself a failed gate.

## 8. Security Boundary

Candidate D may use:

- standard RLWE ciphertexts under a common secret with independent uniform
  masks and independent errors;
- standard scalar GGSW selector ciphertexts;
- public automorphisms;
- public integer-polynomial multiplication;
- standard key switching;
- the circular-security scope already made explicit by the scalar SAB
  baseline.

Candidate D may not use:

- correlated selector errors;
- secret-dependent public sparsity metadata;
- publicly removable encrypted-zero rows;
- a low-rank public mask distribution without a standard reduction;
- an unstated stronger KDM or circular-security assumption.

The security argument must be written as a hybrid over standard RLWE/GGSW
samples. Public late binding does not alter secrecy, but its effect on
correctness and noise must be included.

If closure requires an object outside this boundary, Candidate D is rejected.
It is not silently migrated into a stronger assumption.

## 9. Noise Model

Pairwise equality to scalar SAB is not an absolute correctness test. Candidate
D must derive and measure the error of the bound output.

Let `Sigma_U` be the covariance matrix of the operator channels. A required
covariance-aware bound is:

```text
Var(L_{F_Z}(U))
  <= lambda_max(Sigma_U)
     * sum_{gamma in Gamma} ||gamma(F_Z)||_2^2
```

The analysis must also provide deterministic `L1` or `L-infinity` bounds for
adversarial coefficient alignment. Independence between channels may not be
assumed after shared selector operations unless it is proved.

The bound must explicitly include the selected `Delta`, the supported
coefficient bound of `F_Z`, decomposition error, extraction, and key
switching. Passing the exact finite checker cannot waive this scale-and-noise
gate.

The final gate must:

- test the expected LUT plaintext directly;
- report empirical variance and maximum error;
- derive a parameter-level tail/failure bound;
- compare the failure margin to scalar SAB and exact-dense MAT-SAB; and
- reject a parameter row whose decoding margin is not justified.

One legal parameter adjustment is allowed if it preserves the security target
and the projected performance value. Repeated parameter tuning is prohibited.

## 10. Complexity Model

For binary `SET_2_3_2048`, define:

```text
H = (h + 1) * r_prec * N_in
  = 40 * 7 * 2048
  = 573,440 selector events
```

For `k=1`, `l=1`, exact-dense MAT-SAB performs:

```text
(1 + r)^2 ring products per MAT external product
```

Therefore:

```text
r=2:  9 * H  =  5,160,960 ring products
r=4: 25 * H  = 14,336,000 ring products
```

A scalar RLWE external product has approximately `4*l` ring products for
`k=1`. If Candidate D closes with `g=|Gamma|` channels, its encrypted selector
work is projected as:

```text
4 * l * g * H
```

For the initial `g=2` hypothesis, this is `8*l*H`, independent of the number
of requested LUTs. This count is incomplete until it includes:

- operator initialization;
- all automorphisms;
- late-binding public polynomial products;
- materialization;
- extraction and key switching;
- key size and cache effects; and
- changed noise parameters.

Candidate D may enter encrypted implementation only if the complete Amdahl
projection for `r=4` is at least 10% faster than B1 exact-dense MAT-SAB.

## 11. Implementation Boundaries

Candidate D uses independent types and paths:

```text
SAB_Operator_State
SAB_Operator_Key
operator_sab_*
```

The exact names may follow repository conventions in the implementation plan,
but the ownership boundary is fixed:

- do not change the default behavior of `sab_rlwe_bootstrap`;
- do not replace or remove `sab_pvw_*`;
- do not reuse `MAT_TRGSW` when doing so reintroduces the `(k+r)^2` state;
- keep the new path behind an explicit executable mode or flag;
- separate instrumentation builds from timing builds;
- perform exact checker and reference implementation work before AVX512
  specialization.

No production hot-path permission is granted by this design. Permission is
earned only after the D2/D3 admission gates.

## 12. Baselines

The experiment suite must include:

```text
B0a: current repeated scalar SAB
B0b: repeated scalar SAB with one output secret, independent masks,
     and a shared scalar selector key
B1:  current exact-dense PVW/MAT-SAB
B2:  BatchBoot reproduced locally under a fair backend, or a locally
     implemented equivalent of its relevant EMPmul optimization
D:   LUT-late-binding operator SAB
```

B0b is required to separate algorithmic value from output-key reuse, key-cache
reuse, and implementation artifacts.

The published BatchBoot table may be cited as external context, but it may not
be used to compute this project's speedup. A CCS/USENIX-level result requires
a same-machine B2 reproduction or a combined `D + BatchBoot` path.

Sharing the Mask is a structural and complexity baseline. Its standard TFHE
timings are not directly divided into SAB timings.

## 13. Experimental Protocol

Primary parameter:

```text
BINARY/include-zero SET_2_3_2048
```

Supporting parameters:

```text
SET_4_5_2048
SET_2_3_4096
```

Lane counts:

```text
r = 1, 2, 4, 8
```

`r=1` is a degeneration/negative control. `r=8` runs only after a memory
preflight. The first claim excludes ternary secrets until they pass an
independent closure, noise, correctness, and performance campaign.

Exploratory timing requires at least 10 paired process runs. Final primary
results require at least 30 paired process runs with randomized A/B and B/A
order. The experiment records:

- mean and median;
- standard deviation and coefficient of variation;
- minimum and maximum;
- paired speedup;
- 95% bootstrap confidence interval;
- pre-registered outlier handling;
- CPU affinity, frequency governor, temperature, and background load;
- compiler, flags, FFT backend, and CPU feature set.

Correctness and noise require at least 50 deterministic seeds and at least
`10^6` final plaintext-coefficient observations for promoted rows.

WSL is a correctness and smoke platform. Formal performance results use the
authorized native Linux machine when available.

## 14. Finite Campaign

Candidate D proceeds through:

```text
D0  baseline and state freeze
D1  full-text novelty and claim audit
D2  exact operator-closure checker
D3  correctness, security, noise, and complete-cost admission
D4  isolated encrypted operator primitives
D5  complete binary/include-zero operator SAB
D6  profile-guided implementation optimization
D7  final statistical, correctness, noise, and resource matrix
D8  manuscript, artifact, and independent internal review
```

Candidate D has:

- at most one state-equation revision;
- at most one kernel-layout revision;
- at most one complete-SAB integration attempt.

Failure before D4 prevents encrypted hot-path implementation. Failure at D5
or D6 closes Candidate D instead of starting an optimization loop.

## 15. Single Fallback

Candidate E, an extension-ring or tensor lane-packed SAB, is the only reserved
new-algorithm fallback. It may start only after a recorded Candidate D
rejection.

Candidate E must first:

- map its ring to a standard RLWE or Module-LWE security assumption;
- prove projection and SAB automorphism closure;
- complete a claim-level audit against Batch Bootstrapping I and II; and
- project subquadratic or linear lane cost including projection keys.

Candidate E receives the same one-equation, one-layout, one-integration
budget.

If Candidate E fails, no third mechanism is generated automatically. The
project freezes the exact-dense systems result and any successful BatchBoot
integration, and decides whether those results support a systems/TCHES paper.

## 16. Paper Gate

Candidate D reaches `PAPER_READY` only when:

1. arbitrary supported LUTs are correct in complete SAB;
2. internal ciphertexts and selector keys have a standard RLWE/Module-LWE
   reduction within the approved circular-security scope;
3. correctness and covariance-aware noise theorems are complete;
4. all primary tables use `T/(r*N_active)`;
5. the lower bound of the paired 95% confidence interval is at least 5%
   faster than B1 on the primary row;
6. B2 is locally reproduced or a `D + BatchBoot` combination is evaluated;
7. algorithmic gains are separated from AVX512/backend/key-cache gains;
8. key size, keygen, peak RSS, scratch, and failure margins are reported;
9. novelty wording passes full-text and citation-chain verification; and
10. source, build commands, parameters, seeds, raw logs, and table-generation
    scripts are source-testable.

The intended contribution package is:

- a LUT-late-binding formulation of sparse SAB;
- a bounded operator basis that removes or reduces the dense `Theta(r^2)`
  selector hot path;
- correctness, security-scope, noise, and complexity analysis;
- complete experiments against scalar SAB, exact-dense MAT-SAB, and
  BatchBoot; and
- a reproducible implementation and artifact.

Conference acceptance is external and cannot be guaranteed. The
repository-controlled terminal success state is `PAPER_READY`.

## 17. Verified Literature Anchors

The design is conditioned on the following real sources:

- Guimaraes and Pereira, "Fast Amortized Bootstrapping with Small Keys and
  Polynomial Noise Overhead," ePrint 2025/686 and CCS 2025:
  <https://eprint.iacr.org/2025/686>
- Bergerat et al., "Sharing the Mask: TFHE Bootstrapping on Packed Messages,"
  TCHES 2025(4):
  <https://doi.org/10.46586/tches.v2025.i4.925-971>
- Li et al., "BatchBoot: Fast Batched Bootstrapping for TFHE scheme and
  Practical Applications," USENIX Security 2026:
  <https://www.usenix.org/conference/usenixsecurity26/presentation/li-zhihao>
- Lin and Wu, "Practical Amortized Bootstrapping for NTRU-Based FHE,"
  ePrint 2026/068:
  <https://eprint.iacr.org/2026/068>
- Carpov, Izabachene, and Mollimard, "New Techniques for Multi-value Input
  Homomorphic Evaluation," ePrint 2018/622:
  <https://eprint.iacr.org/2018/622>
- Kluczniak and Schild, "FDFB^2: Functional Bootstrapping via Sparse
  Polynomial Multiplication," ePrint 2024/1376:
  <https://eprint.iacr.org/2024/1376>
- Guimaraes, Borin, and Aranha, "MOSFHET: Optimized Software for FHE over
  the Torus," ePrint 2022/515:
  <https://eprint.iacr.org/2022/515>
- Liu and Wang, "Batch Bootstrapping I" and "Batch Bootstrapping II,"
  EUROCRYPT 2023:
  <https://doi.org/10.1007/978-3-031-30620-4_11>
  and <https://doi.org/10.1007/978-3-031-30620-4_12>

The literature search remains open until the manuscript search-freeze date.
No source supports a claim that Candidate D is already novel or correct.
FDFB^2 is a critical novelty kill gate because it already claims evaluation
of an arbitrary number of functions for only constant additional cost.
Candidate D must provide a distinct SAB-specific operator theorem and
complexity result, plus a complete measured advantage or complementary
composition. A specialization or reimplementation of FDFB^2 is rejected as
the primary paper contribution.

## 18. Approved Transition

The user approved:

1. the Candidate D architecture;
2. the correctness, security, noise, and stopping gates;
3. the experiment and implementation boundaries; and
4. the finite campaign and paper gate.

After this written specification is reviewed, the next permitted action is to
write a detailed implementation plan. Algorithm code remains blocked until
that plan is reviewed and its D2/D3 gates are executed.
