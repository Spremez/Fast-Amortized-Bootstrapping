# Stage212 Multirow FFT API Probe Plan

Decision: `PASS_STAGE212_MULTIROW_WRAPPER_PROMOTE_STAGE213`.

Loop:

1. Hypothesis: a source-local multirow reverse-DFT wrapper can reduce per-row
   conversion/copy overhead enough to justify later SAB integration.
2. Implementation: standalone probe only; no production SAB code.
3. Correctness gate: wrapper outputs must match `execute_reverse_torus64`
   exactly for 3-row and 5-row groups.
4. Performance gate: best wrapper must reach at least `1.03x`
   speedup for both row groups.
5. Exit: promote only to a later flag-only SAB preflight, or close the local
   wrapper route and move to native counters or a true backend batch FFT design.
