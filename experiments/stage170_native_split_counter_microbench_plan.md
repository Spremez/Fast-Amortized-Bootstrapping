# Stage170 Validation Plan

Goal: measure separate native hardware counters for MAT EP/subdecomp and
from_DFT materialization under the current exact r=6 PVW/MAT-SAB path.

Protocol:

- remote: CB5 native Linux via SSH, directory `/home/delld/spz/spz` equivalent
  user workspace;
- backend: `spqlios_avx512`;
- flags: `FFT_LIB=spqlios_avx512 A_PRNG=none ENABLE_VAES=false ENABLE_PVW_TMLWE=true MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true MAT_TRGSW_AVX512_RGT4_FUSED=true SAB_PVW_BACKEND_FROM_DFT_ADD=true SAB_PVW_SUB_DECOMP_FUSION=true`;
- parameters: `r=6`, `N=2048`, `Bg_bit=23`,
  `items=256`, `reps=8`, `warmups=2`;
- variants:
  - `mat_ep_subdecomp`;
  - `from_dft_materialize`;
- counters: `cycles,instructions,cache-references,cache-misses,branches,branch-misses,mem_inst_retired.all_loads,mem_inst_retired.all_stores,fp_arith_inst_retired.512b_packed_double,fp_arith_inst_retired.256b_packed_double`.

Acceptance:

- both probe correctness checks pass;
- both perf runs exit successfully;
- cycles, instructions, load/store, and FP512 counters are present for both
  variants;
- remote `perf_event_paranoid` is restored to its pre-run value.

Failure handling:

- if counters cannot be isolated, retain only full-run Stage167 attribution;
- if correctness fails, discard all performance data for this stage;
- if from_DFT or MAT EP dominates differently than expected, route the next
  optimization stage from data rather than from prior intuition.
