# Stage87 H14 Backend FromDFT-Add Preflight Plan

## Goal

Implement the Stage86-selected H14-C1 materialization candidate behind
`SAB_PVW_BACKEND_FROM_DFT_ADD` and test whether backend-level
`FromDFT(dft) + addend` output conversion can beat the existing
wrapper-level `pvmtmlwe_from_DFT_add` path.

## Commands

Primary WSL/Linux AVX512 preflight:

```bash
FFT_LIB=spqlios_avx512 \
SAB_PVW_BENCH_R=6 \
SAB_PVW_BENCH_REPS=1 \
bash scripts/run_stage87_h14_backend_from_dft_add_preflight.sh
```

Portable smoke build used during implementation:

```bash
make -B FFT_LIB=ffnt A_PRNG=none ENABLE_VAES=false PARAM=SET_2_3 \
  SAB_PVW_KERNEL_TEST=true SAB_PVW_BACKEND_FROM_DFT_ADD=true ARCH_FLAGS= -j4
./main
```

## Gates

| gate | requirement |
|---|---|
| explicit flag | `SAB_PVW_BACKEND_FROM_DFT_ADD` is opt-in and also enables wrapper CMUX fused add |
| correctness | WSL `spqlios_avx512` staged CMUX/RGSW/MAT gate and target full-output gate pass |
| full-SAB smoke | r=6 backend-add one-run PVW latency is lower than wrapper-level fused baseline |
| promotion policy | one-run smoke can only open repeated/noise/resource Stage88 gates |

## Failure Handling

If correctness fails, revert the candidate or repair the backend conversion
before running performance. If full-SAB is neutral or negative, keep the flag as
an implementation ablation and return to candidate routing. If only the one-run
smoke is positive, do not promote; Stage88 must run repeated A/B, noise, and
resource gates.
