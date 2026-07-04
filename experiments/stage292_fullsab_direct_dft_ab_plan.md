# Stage292 Experiment Plan

Goal: validate Stage291 direct sub-decompose-to-DFT inside full SAB.

Comparison:

- selected_control: current selected r=4 include-zero PVW-SAB path.
- direct_dft_candidate: selected_control plus
  `MAT_TRGSW_SUB_DECOMP_DFT_DIRECT=true`.

Correctness gate: both variants must print
`SAB_PVW_NONBINARY_BENCH correctness ... Pass`.

Performance gate: use complete SAB `T_bootstrap/r`. Promote only if direct DFT
improves the selected control by at least 1.02x in mean repeated local runs.

Failure handling: if neutral or negative, keep Stage291 as a kernel-level
ablation and do not default-enable the flag.
