# Stage261 Non-Binary Target T_bootstrap/r Preflight

Decision: `PASS_STAGE261_NONBINARY_TARGET_PER_BIT_PREFLIGHT`.

Stage261 adds an explicit target-parameter benchmark for the non-binary
PVW/MAT-SAB full bootstrapping path. The comparison is the intended amortized
dimension:

```text
T_bootstrap / r
```

The PVW/MAT path processes one r-body ciphertext with r independent LUT/SAB
lanes. The scalar baseline is r repeated scalar SAB bootstraps using matching
per-lane output keys and LUTs. Therefore `speedup_vs_scalar_repeated` is also
the speedup of amortized time per processed plaintext lane/bit, not a
single-output latency claim.

## Parameters

| item | value |
| --- | --- |
| parameter set | SET_2_3 |
| input ring | N=2048, k=1 |
| output ring | N=2048, k=1 |
| SAB sparsity | h=39 |
| monomial precision | r_prec=7 |
| bootstrapping decomposition | l=1, bg_bit=23 |
| message precision | prec=3 |
| packing KS | ell=2, bg_bit=14 |
| HW KS | ell=12, bg_bit=1 |
| backend | WSL2/Linux spqlios_avx512 |
| MAT AVX512 variant | MAT_TRGSW_AVX512_SMALLR_SPECIALIZED |
| input branches | include-zero and ternary |

## Results

| mode | r | reps | correctness_gate | pvw_avg_us | scalar_repeated_avg_us | t_bootstrap_over_r_pvw_us | t_bootstrap_over_r_scalar_us | speedup_vs_scalar_repeated |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| include_zero | 2 | 1 | Pass | 16426335.000 | 21079914.000 | 8213167.500 | 10539957.000 | 1.283 |
| ternary | 2 | 1 | Pass | 16717367.000 | 21517129.000 | 8358683.500 | 10758564.500 | 1.287 |
| include_zero | 4 | 1 | Pass | 30921155.000 | 42896831.000 | 7730288.750 | 10724207.750 | 1.387 |
| ternary | 4 | 1 | Pass | 31113229.000 | 42163428.000 | 7778307.250 | 10540857.000 | 1.355 |

## Interpretation

The preflight result is positive: all four target rows pass PVW/scalar phase
equivalence and the complete SAB amortized metric improves by
`1.283x-1.387x` on the same backend.

This does not prove theoretical optimality. The run count is one per row, WSL2
is a proxy performance platform, and Stage261 does not include perf counters,
assembly attribution, r=1 negative control, or native Linux confidence
intervals. The correct next step is repeated native/backend-fair measurement
plus profile attribution before making a final paper claim.

## Claim Boundary

| claim | status | allowed_wording | forbidden_wording |
| --- | --- | --- | --- |
| nonbinary_target_per_bit_preflight | supported_preflight | On WSL2/Linux spqlios_avx512, the target SET_2_3 non-binary PVW/MAT-SAB path passes complete SAB correctness and shows 1.283x-1.387x T_bootstrap/r speedup for r=2/4. | The implementation has reached theoretical optimum or paper-grade final speedup. |
| amortized_metric_definition | supported | The comparison dimension is full SAB time divided by r output lanes, with scalar baseline measured as r repeated scalar SAB calls. | The speedup is a single-output latency speedup over scalar SAB. |
| nonbinary_final_performance | not_final | Stage261 admits repeated/statistical performance validation. | Stage261 alone is sufficient for a publication performance claim. |
| mat_avx_theoretical_optimum | unsupported | The Stage261 harness uses the current small-r MAT AVX512 specialization. | The MAT external product AVX512 implementation is theoretically optimal. |

## Proof Gate

| gate | status | metric | value | interpretation |
| --- | --- | --- | --- | --- |
| G1_harness | PASS | nonbinary target benchmark flag | SAB_PVW_NONBINARY_BENCH | Explicit target full SAB T_bootstrap/r harness exists. |
| G2_correctness | PASS | target full PVW/scalar phase equivalence | 4/4 | Each measured row first compares PVW lane output against repeated scalar SAB. |
| G3_branch_coverage | PASS | mode/r coverage | include_zero:r2,include_zero:r4,ternary:r2,ternary:r4 | Preflight covers include-zero and ternary for r=2 and r=4. |
| G4_same_backend_speed | PASS | speedup_vs_scalar_repeated | 1.283x..1.387x | Same spqlios_avx512 backend comparison, measured as complete SAB T_bootstrap/r. |
| G5_statistics | PREFLIGHT_ONLY | reps | 1 per row | This is not yet a statistical paper-grade speed claim. |
| G6_decision | PASS_STAGE261_NONBINARY_TARGET_PER_BIT_PREFLIGHT | stage decision | PASS_STAGE261_NONBINARY_TARGET_PER_BIT_PREFLIGHT | Proceed to repeated/native/profiled Stage262+ validation. |

Generated from input head `62342a9`.
