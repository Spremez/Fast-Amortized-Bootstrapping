# Stage158 Experiment Plan

Goal: test whether Stage157 sub-decompose fusion improves complete SAB
`T_bootstrap/r`.

Platform: WSL/Linux with `FFT_LIB=spqlios_avx512`.

Control: H14 r=6 backend current-head path.

Candidate: same flags plus `SAB_PVW_SUB_DECOMP_FUSION=true`.

Correctness gate: both variants must print `SAB_PVW_BENCH correctness ... Pass`.

Performance gate: candidate/control on `T_bootstrap/r`; positive smoke requires
later repeated/noise/resource gates before any promotion.
