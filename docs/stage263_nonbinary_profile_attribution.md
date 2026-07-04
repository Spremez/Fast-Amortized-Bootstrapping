# Stage263 Non-Binary Profile Attribution

Decision: `PASS_STAGE263_NONBINARY_PROFILE_ATTRIBUTION`.

Stage263 profiles the same target `T_bootstrap/r` non-binary PVW/MAT-SAB path
from Stage262. The profile is attribution evidence only; speed claims still use
the non-instrumented repeated Stage262 results.

## Profile Metrics

| mode | r | count_gate | full_us | pvw_avg_us | speedup_vs_scalar_repeated | mat_ep_share_of_body | from_dft_share_of_body | add_share_of_body | sub_share_of_body | sub_a_share_of_body | postproc_residual_share_of_pvw |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| include_zero | 2 | PASS | 16333908.000 | 16496208.000 | 1.273 | 0.361283 | 0.231988 | 0.141289 | 0.145719 | 0.103446 | 0.009839 |
| ternary | 2 | PASS | 16844564.000 | 17022729.000 | 1.269 | 0.357140 | 0.226120 | 0.139759 | 0.144319 | 0.116951 | 0.010466 |
| include_zero | 4 | PASS | 30726595.000 | 30990258.000 | 1.359 | 0.415161 | 0.207560 | 0.130874 | 0.126459 | 0.110166 | 0.008508 |
| ternary | 4 | PASS | 31692418.000 | 31991920.000 | 1.333 | 0.418790 | 0.205030 | 0.123440 | 0.121523 | 0.121316 | 0.009362 |

## Interpretation

All rows preserve the target schedule counts: `573440` MAT external-product /
CMUX updates, `5080` NCMUX updates, `39` non-binary `sub_a` calls, and zero
copyback calls. This confirms Stage262 speedups are not caused by changing the
SAB schedule length.

MAT external product is the largest single measured body component
(`0.357-0.419` of body time), but non-MAT body work is still
large (`0.581-0.643`). Therefore the next optimization
must start with a MAT AVX512 counter/assembly audit, while preserving Amdahl
discipline: kernel-only improvements cannot be presented as complete SAB
speedups until full `T_bootstrap/r` A/B passes.

## Next Priority

| priority | target | profile_basis | candidate | stop_rule |
| --- | --- | --- | --- | --- |
| P1 | MAT external product body | mat_ep/body=0.357..0.419 | native perf/assembly audit for load/store/FMA pressure; compare generic vs small-r MAT AVX512; only then implement layout/tiling changes | do not claim theoretical optimum without counters and same-backend full SAB A/B |
| P2 | from_DFT/add materialization | from_DFT+add is material but below MAT EP | revisit backend from_DFT_add only if MAT counter audit shows kernel headroom is exhausted | avoid repeating prior neutral H14 work unless current profile changes the share materially |
| P3 | non-binary sub_a | sub_a/body max=0.121 | design a mode-specific sub_a selector/rotation profile before code changes | must beat full SAB A/B; sub_a-only speedup has limited Amdahl ceiling |
| P4 | post-processing/extract/KS | postproc residual/PVW max=0.010 | defer unless body optimizations increase the residual share | do not add high-risk tail optimizations for low single-digit share |

## Proof Gate

| gate | status | metric | value | interpretation |
| --- | --- | --- | --- | --- |
| G1_correctness | PASS | PVW/scalar target correctness | 4/4 | Profile rows retain full target phase equivalence. |
| G2_schedule_counts | PASS | CMUX/MAT/NCMUX/sub_a/copyback counts | include_zero:r2 cmux=573440 mat_ep=573440 ncmux=5080 sub_a=39 copyback=0;ternary:r2 cmux=573440 mat_ep=573440 ncmux=5080 sub_a=39 copyback=0;include_zero:r4 cmux=573440 mat_ep=573440 ncmux=5080 sub_a=39 copyback=0;ternary:r4 cmux=573440 mat_ep=573440 ncmux=5080 sub_a=39 copyback=0 | Non-binary profile preserves target SAB schedule: 573440 MAT EP/CMUX, 5080 NCMUX, 39 sub_a, zero copyback. |
| G3_component_attribution | PASS | MAT EP body share | 0.357..0.419 | MAT EP remains the largest single measured body component but not the whole bottleneck. |
| G4_non_mat_bound | PASS | non-MAT body share | 0.581..0.643 | Amdahl bound prevents kernel-only changes from explaining all remaining SAB cost. |
| G5_tail_bound | PASS | max postproc residual/PVW | 0.010 | Post-processing residual is visible but below the body-dominant region. |
| G6_decision | PASS_STAGE263_NONBINARY_PROFILE_ATTRIBUTION | stage decision | PASS_STAGE263_NONBINARY_PROFILE_ATTRIBUTION | Proceed to MAT AVX512 memory/FMA counter audit and sub_a/materialization secondary hypotheses. |

## Claim Boundary

| claim | status | allowed_wording | forbidden_wording |
| --- | --- | --- | --- |
| nonbinary_schedule_invariant | supported_profile | The target non-binary PVW/MAT-SAB profile preserves the expected SAB schedule counts for r=2/r=4 include-zero and ternary. | The profile proves native paper-grade performance. |
| dominant_component | supported_profile | MAT EP is the largest single measured body component at 0.357-0.419 of body time, while non-MAT body work remains 0.581-0.643. | Only the MAT kernel matters for final SAB speed. |
| mat_avx512_theoretical_optimum | unsupported | Stage263 identifies MAT EP as the first counter-audit target. | The current MAT AVX512 implementation is theoretically optimal. |

Generated from input head `727d986`.
