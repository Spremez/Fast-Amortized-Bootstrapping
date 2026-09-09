# M-A3 / I-2 tight closure: per-step noise profiler (dell, 2026-09-09)

Instrument: `src/probe_rinput_prof.c` (dell build_fin, AVX-512 + spqlios,
same objects as stage403). Theory: `theory_checks/stage405_noise_master_theorem.md`
(N-EP four-term identity, DC-walk theorem N-DC, pipeline recursion N1).
This file replaces the stage403 reconciliation BRACKET with the tight
closed-form prediction (6r duty: algorithm theory -> formal proof ->
machine adjudication -> experiment, no guessing anywhere in the chain).

## Results (6 trials per point, ALL PASS both points)

| Point | Gates | STAGE worst \|lr\| | FINAL lr | PAIR lr | BENCH ratio |
|---|---|---|---|---|---|
| n=256/h=6/rp=7 (out 2048) | 6/6 (0/512) | **0.171** | −0.01 | **+0.28** | 1.232x |
| n=512/h=8/rp=9 (out 2048) | 6/6 (0/1024) | **0.186** | −0.00 | **+0.24** | 1.315x |

All per-stage |log2 ratio| <= 0.38 (i.e. within 1.3x) at EVERY stage of
EVERY trial; final noise and pair reconciliation close to <= 0.3 bit.

## Primitive closure (mean of 6; derived vs measured, bits log2)

| Primitive | Derived | Measured P1 / P2 |
|---|---|---|
| eps (EP-side residual, one-sided U[0,2^41)) | rms 2^40.26 (mu 2^40, sigma 2^39.21) | 40.22 / 40.22 |
| ks_h (aut-KS w=1+N) = sqrt(hw)*sigma_eps | 2^44.19 | 44.44 / 44.44 |
| ks_m1 (aut-KS w=2N-1) | 2^44.19 | 44.30 / 44.27 |
| **ep1 = DC-walk mu_eps*N/sqrt(12)** | **2^49.20** | 49.19 / 49.19 |
| ep0 = digits(x)e_kg + DFT-num | 2^43.4 | 43.37 / 43.43 |
| ep_s (first bit, own selector, setup operands) | ~2^44.3 | 44.33 / 44.04 |
| psi = sqrt(ks_m1^2 + ks_h^2/2) | 2^44.63 | 44.45 / 44.40 |
| suba = ks_h/sqrt(2) (from measured ks_h: 2^43.94) | 2^43.94 | 43.73 / 43.76 |
| DCWALK w_rms (theory hw*mu/sqrt3 = N*mu/sqrt12) | 2^49.20 | 49.18-49.21 |

XCHECK note: the "ep1/ks_h ~ 1" label in the probe output is STALE (from
the obsolete model where ep1 was believed epsilon(x)s-dominated); the
correct relation is ep1 = DC-walk (N-DC), which is what closes.

## Mechanism chain (all machine-adjudicated this session)

1. Two decomposition conventions in the library: EP side
   (pvmtmlwe_decompose, offset 2^63) -> ONE-SIDED residual U[0,2^41);
   KS side (polynomial_decompose_i, offset 2^63+2^40) -> BALANCED
   residual (round-to-nearest). Hence KS has no DC, EP has.
2. EP noise identity (exact, integer-adjudicated max dev = 0):
   phi_EP = dec(D.a)(x)e_0 + dec(D.b)(x)e_1 + m*(eps_a (x) s - eps_b) + nu_DFT.
3. DC-walk: E[eps_a (x) s] = mu_eps*(2H(i)-hw) -- a monotone staircase from
   -hw*mu to +hw*mu; rms over coefficients = mu_eps*N/sqrt(12) = 2^49.2.
   Same pattern EVERY m=1 event (depends only on the key) -> COHERENT
   linear accumulation within phases (observed: 4 events -> exactly 4x),
   partial decorrelation across phases by U_a Y-shifts.
4. Prediction = per-slot deterministic DC polynomial (exact integer
   arithmetic through wraps/sub_a/doubling) + quadratic white track with
   event-counted weights. Stage-level reconciliation 0.17-0.19 bits worst.
5. Odd-tail (lane-1 tail columns, non-extraction): 2^57-2^61.8 class
   deviations, fold-alias of >=2^63 pseudo-class at columns without the
   guard invariant; ZERO effect on extraction channel / gate / pair /
   GF(257). Characterized open item (stage405 §8).

## Errata closed here (see stage405 §9)

- stage403 upper-model sigma_EP synthetic calibration measured MESSAGE
  DIFFERENCES as noise (selector bit=1: phase(R)-phase(A) contains
  msg_B-msg_A ~ 2^61). Correct reference = the SELECTED input.
- stage396 §4 (HT-6 old form) superseded by HT-6' (stage405 §5): missing
  EP terms + DC coherence; the "rho ~ U(±1/2)*2^63" rescale-rounding term
  does not exist (integer (c+1)>>1 rounding is +-1 unit).

## Implementation-level optimization candidate (recorded, NOT applied)

pvmtmlwe_decompose with a half-digit offset (round-to-nearest, like the
KS side) kills mu_eps -> per-m=1-EP noise drops from 2^49.2 to ~2^44.5
(-4.7 bits). Not applied now (would change measured baselines); flagged
for the paper's implementation notes + future rerun.

## Artifacts

- Raw logs: point1_h6.log, point2_h8.log (this dir; dell original:
  ~/spz/dell-final-bench/repro_stage405/)
- Probe: src/probe_rinput_prof.c (MICRO adjudication mode:
  SAB_RINPUT_MICRO=1; AES-operand mode: SAB_RINPUT_AES=1)
- Build (dell): canonical FLAGS + link with -Wl,--allow-multiple-definition
  and trailing spqlios-fft-impl-avx512.o (same as stage403)

## I-6 FINAL-parameter closure (dell, 2026-09-09 late; closes review attack N-5)

Run: n=2048, h=42, rho=7, sigma_G=2^-49, out 2048, coarse measurement
(suba + final stages), 1 trial. RS keygen bug fixed first: the 6th arg
of RS_sparse_binary_key is target_r_prec (not a gap bound); target 6
exhausts the internal 2^15-attempt loop at n=2048/h=42 (acceptance
~1/81000) leaving a garbage pointer (SIGSEGV) -- target = 7 (the FINAL
design rho, acceptance ~1/22) + null-guard added.

| Quantity | Value |
|---|---|
| Gate | **0/4096 PASS** |
| Primitives | eps 40.22; ks_h 44.09; ks_m1 44.24; ep1 49.15; ep0 43.43; psi 44.56; suba 43.46; ep_s 43.66 |
| DCWALK | hw=984, w_rms **49.15** (= derived mu*N/sqrt12 49.20 within 0.05 bit) |
| FINAL (doubled, even class) | meas 2^54.57 = pred 2^54.57 (**-0.00 bit**; extrapolation band was 2^55-56) |
| PAIR | 2^53.60 vs pred 2^53.57 (**+0.03 bit**) |
| Stage gate | worst 0.020 |
| Mirror vs stock | bit-identical |
| Bench | interleaved 14.43 s vs 2x-scalar 11.71 s = 1.232x |

sigma_kg note: with sigma_G = 2^-49 the selector-keygen noise stays at
the ~2^16 empirical floor (ep0 43.43 unchanged vs toy 43.37-43.51), so
the toy-calibrated primitives carry over; the noise master theorem
closes at FINAL parameters with the same constants.
