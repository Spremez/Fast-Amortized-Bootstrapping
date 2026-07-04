# Stage262 Non-Binary Target Repeated Stats

Decision: `PASS_STAGE262_NONBINARY_TARGET_REPEATED_STATS`.

Stage262 repeats the Stage261 target benchmark with `reps=3` and adds r=1 as a
negative control. The metric remains:

```text
T_bootstrap / r
```

The comparison is still complete SAB PVW/MAT with r output bodies against r
repeated scalar SAB bootstraps on the same backend.

## Summary

| mode | r | reps | correctness_gate | t_bootstrap_over_r_pvw_us | t_bootstrap_over_r_scalar_us | speedup_vs_scalar_repeated | speedup_stddev |
| --- | --- | --- | --- | --- | --- | --- | --- |
| include_zero | 1 | 3 | Pass | 10704410.000 | 10702207.333 | 1.000 | 0.021 |
| ternary | 1 | 3 | Pass | 10654346.333 | 10743326.667 | 1.008 | 0.017 |
| include_zero | 2 | 3 | Pass | 8339109.833 | 10606723.167 | 1.272 | 0.010 |
| ternary | 2 | 3 | Pass | 8240169.833 | 10622105.000 | 1.289 | 0.017 |
| include_zero | 4 | 3 | Pass | 7750110.333 | 10596985.417 | 1.367 | 0.010 |
| ternary | 4 | 3 | Pass | 7861032.333 | 10724168.750 | 1.364 | 0.002 |

## Interpretation

The r=1 rows remain near parity: maximum absolute distance from 1.0 speedup is
`0.008`. The r=2/r=4 rows retain stable same-backend amortized
speedup of `1.272x-1.367x` with maximum
reported speedup standard deviation `0.021`.

This supports the intended interpretation: PVW/MAT-SAB is improving amortized
time per output body/lane, not single-body latency. It is still WSL2 evidence;
the next research gate must attribute the speedup with native Linux profiling
and MAT AVX512 memory/FMA counters.

## Proof Gate

| gate | status | metric | value | interpretation |
| --- | --- | --- | --- | --- |
| G1_correctness | PASS | target full PVW/scalar phase equivalence | 6/6 | Every repeated-stat row performs a correctness comparison before timing. |
| G2_coverage | PASS | mode/r coverage | include_zero:r1,include_zero:r2,include_zero:r4,ternary:r1,ternary:r2,ternary:r4 | Covers r=1/2/4 for include-zero and ternary. |
| G3_negative_control | PASS | max abs(r=1 speedup - 1) | 0.008 | r=1 remains near parity, supporting the lane-amortization interpretation. |
| G4_target_speed | PASS | r=2/4 speedup range | 1.272x..1.367x | Repeated WSL same-backend target rows retain amortized speedup. |
| G5_variability | PASS | max speedup stddev | 0.021 | Three-repetition rows show low local variation; still not native paper-grade evidence. |
| G6_decision | PASS_STAGE262_NONBINARY_TARGET_REPEATED_STATS | stage decision | PASS_STAGE262_NONBINARY_TARGET_REPEATED_STATS | Proceed to profile attribution and MAT AVX512 limit analysis. |

## Claim Boundary

| claim | status | allowed_wording | forbidden_wording |
| --- | --- | --- | --- |
| target_repeated_t_bootstrap_over_r | supported_wsl_repeated | On WSL2/Linux spqlios_avx512, repeated target measurements show r=2/4 non-binary PVW/MAT-SAB T_bootstrap/r speedup of 1.272x-1.367x. | This is the final native Linux or paper-grade performance claim. |
| lane_amortization_interpretation | supported_by_negative_control | r=1 stays within 0.008 of parity, while r=2/4 shows stable speedup, supporting the multi-body amortization interpretation. | The MAT path is intrinsically faster for a single scalar body. |
| mat_avx512_theoretical_optimum | unsupported | Stage262 measures the current small-r AVX512 implementation in full SAB. | Stage262 proves the AVX512 MAT kernel is at its theoretical optimum. |

Generated from input head `fb80c97`.
