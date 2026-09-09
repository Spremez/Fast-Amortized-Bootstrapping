# I-2/I-3: r-input noise reconciliation + benchmark (dell, 2026-09-09)

Machine: dell (AVX-512, spqlios), same-build pairing, 6 trials each point.
Probe: probe_rinput (REPS loop + KS/EP calibration + M-HT.4 reconciliation).

## Point 1: in_N=256, out_N=2048 (d=1024), h=6, r_prec=7, prec=3

- GATES: 6/6 ALL PASS (0/512 per trial; G0 setup 0)
- pair noise: max 2^54.23, rms 2^53.99 (budget ≫)
- BENCH (median of 6): interleaved 305-313 ms, 2x-scalar 214-229 ms,
  ratio **1.35-1.40x** (runs: 1.388/1.351/1.356/1.376/1.365/1.399)
- Calibration: sig_s 2^46.17, sig_KS 2^44.26 (LCG mask), sig_EP 2^60.63
  (synthetic random-mask CMUX, upper bound)
- Reconciliation: measured 2^53.99 bracketed by
  [lower-model 2^46.75 (KS+scalar only), upper-model 2^63.94 (+49 EP
  full-weight)] -- conservative Pass; tight (<1.3) calibration deferred to
  M-A3 per-step profiler.

## Point 2: in_N=512, out_N=2048 (d=1024), h=8, r_prec=9

- GATES: 6/6 ALL PASS (0/1024 per trial)
- pair noise: max 2^54.64, rms 2^54.30
- BENCH (median of 6): interleaved 1075.6 ms, 2x-scalar 746.9 ms,
  ratio **1.440x**
- Reconciliation bracket: [2^46.x, 2^64.29], measured 2^54.30 inside.

## Notes for paper

- r-input interleaved is ~1.35-1.44x the cost of 2 scalar bootstraps
  (toy params, standard kernel): expected sign (Hom-Tr adds 1 aut-KS +
  4 monomial muls per slot per step + wraps); the ABSOLUTE amortized
  claim for r-input is semantic (2 inputs in one blind rotation), not
  speedup vs r scalar runs at these toy sizes.
- The pair-noise bracket vs models is honest: the simple M-HT.4
  lower model under-predicts (missing EP term); the synthetic-EP upper
  model over-predicts (synthetic masks overstate in-pipeline EP);
  tight per-step profiling = M-A3 obligation.
