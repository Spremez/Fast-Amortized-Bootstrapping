# pvw_sab_r4_unrolled_avx512: r=4 Row-Unrolled MAT AVX512 External Product

## Summary

- Parent algorithm: PVW/MAT-SAB complete bootstrapping path for 2025/686 sparse amortized bootstrapping.
- Focused module: `mat_trgsw_mul_pvmtmlwe_DFT`, `k=1,l=1,r=4`, AVX512 MAT external product.
- Optimization target: reduce hot-loop pointer chasing and row-loop overhead inside the r=4 MAT external product.
- Status labels: `[experiment pending]`, `[kernel-level only until full SAB A/B]`, `[not a default path]`.
- Main hypothesis: explicitly hoisting all five decomposed-row pointers and selector-output pointers outside the coefficient loop, then unrolling rows 1-4, may reduce instruction overhead enough to improve r=4 MAT microbench and possibly complete-SAB throughput.

## Mathematical Definition

The external product remains the same dense MAT accumulation:

```text
out_y = sum_{row=0}^{k+r-1} dec(row, in) * selector[row][y]
for y in {a_0, b_0, b_1, b_2, b_3}, with k=1,r=4,l=1.
```

The variant changes only the implementation schedule for the same terms:

```text
baseline:    coefficient loop contains a row loop and reloads row selector pointers.
variant:     coefficient loop has rows 0..4 explicitly expanded with row pointers fixed before the loop.
```

## Pseudocode

```text
Input: PVW_TMLWE in, MAT_TRGSW_DFT selector, scratch dec_dft
Output: PVW_TMLWE_DFT out
1. Decompose in into five rows and convert each row to DFT.
2. Bind dec0..dec4 and selector row/output pointers once.
3. For each AVX512 coefficient block:
4.   Initialize five output accumulators from row 0.
5.   Add rows 1, 2, 3, and 4 with explicit complex FMA sequences.
6.   Store a_0 and b_0..b_3 accumulators.
```

## Delta From Original Algorithm

| Original component | Variant component | Relationship | Evidence/status |
| --- | --- | --- | --- |
| `mat_trgsw_mul_pvmtmlwe_DFT_k1_l1_r4_avx512` row loop | `mat_trgsw_mul_pvmtmlwe_DFT_k1_l1_r4_unrolled_avx512` explicit rows | implements same arithmetic with different instruction schedule | Stage65A |
| MAT key layout | unchanged MAT_TRGSW_DFT row-major layout | no key-format change | required invariant |
| scalar SAB baseline | unchanged | no scalar behavior change | required invariant |
| promoted PVW path | unchanged unless compile flag is set | explicit ablation only | required invariant |

## Complexity Change

- Time: same asymptotic dense MAT multiply count, potentially fewer scalar pointer loads and loop-control instructions.
- Memory: no additional key, scratch, or accumulator storage.
- Communication or IO: unchanged.
- What must be measured: staged kernel microbench, instruction proxy, full r=4 SAB A/B, and final-output noise if full-SAB smoke is positive.

## Theory Dependencies

- Inherited assumptions: PVW/MAT external product correctness, active-buffer SAB lane invariant, binary target parameter semantics.
- Relaxed/new assumptions: none.
- Proof steps affected: none at the protocol level; this is an implementation schedule variant.
- New lemmas needed: none for correctness; performance claims need empirical evidence.
- Current status: implementation and smoke evaluation required.

## Potential Failure Reasons

- Failure mode: compiler already hoists/unrolls enough, so explicit source unrolling is neutral.
- Trigger condition: instruction proxy or microbench does not improve.
- How to detect: compare specialized baseline versus `r4_unrolled` in Stage65A CSVs.
- Mitigation or follow-up: keep as neutral ablation; do not default-enable.

- Failure mode: higher register pressure causes spills or worse full-SAB throughput.
- Trigger condition: kernel improves but full-SAB r=4 is neutral or slower.
- How to detect: full-SAB smoke and repeated A/B.
- Mitigation or follow-up: reject promotion; use native perf counters before further r=4 tiling.

## Required Experiments

- Baselines: current `MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true` r=4 active-buffer PVW/MAT-SAB path.
- Datasets: deterministic synthetic FHE test inputs from the existing `SAB_PVW_KERNEL_TEST` and `SAB_PVW_BENCH` harnesses.
- Metrics: MAT `mat_avg_us`, full-output MAT `mat_avg_us`, complete-SAB `pvw_avg_us`, speedup versus repeated scalar, objdump instruction proxy.
- Ablations: `specialized` versus `r4_unrolled` under the same `spqlios_avx512` backend.
- Complexity runs: instruction proxy via `objdump`, with native counters still blocked until Stage61/Stage37 unlocks.
- Robustness runs: r=4 staged kernel pass, complete-SAB correctness pass, repeated full-SAB A/B if smoke is positive.
- Statistical checks: repeated full-SAB runs before promotion; one-run smoke cannot support a bootstrapping claim.
- Success criteria: full-SAB repeated r=4 improvement over current specialized path with correctness/noise/resource gates preserved.
- Failure criteria: correctness failure, kernel negative result, full-SAB neutral/negative result, or register-pressure evidence that cannot be explained without native counters.

## Paper Contribution Candidate

`[experiment pending]` The variant is at most an implementation ablation showing whether explicit r=4 row-unrolling can improve a MAT external product inside PVW/MAT-SAB. It is not a novelty claim and cannot be described as SAB bootstrapping acceleration unless complete-SAB repeated benchmarks and noise/resource gates pass.
