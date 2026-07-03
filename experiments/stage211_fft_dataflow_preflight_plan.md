# Stage211 FFT/DFT Dataflow Preflight Plan

Decision target: `PASS_STAGE211_DFT_DATAFLOW_PREFLIGHT_DENY_HOTPATH_CODE`.

Research loop:

1. Hypothesis: the Stage209 `torus_to_dft_rows` cost can only justify code if
   a mechanism differs from old same-format batching/direct-scale attempts.
2. Theory model: exact MAT-EP currently performs coefficient-domain
   decomposition, row-wise torus-to-DFT conversion, then DFT-domain addmul.
   A conversion shortcut must either supply a new exact backend primitive or
   prove representation closure and noise behavior.
3. Implementation boundary: Stage211 writes no production SAB hot-path code.
   It records whether implementation is admitted, blocked, or denied.
4. Gate: old routes remain denied; a new multirow FFT/backend API is admitted
   only as a Stage212 standalone probe.
5. Exit: if no concrete primitive exists, move to Stage212 API/probe or native
   counter refresh instead of repeating theory.
