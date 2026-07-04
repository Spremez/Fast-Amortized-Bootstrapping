# Stage264 MAT-AVX512 Counter/Assembly Preflight

Decision: `PASS_STAGE264_MAT_AVX512_COUNTER_PREFLIGHT_PROXY_ONLY`.

Stage264 answers a narrow question: whether the current MAT external-product
AVX512 path can be treated as theoretically optimal. It cannot. The source
model supports the MAT-aware memory-traffic hypothesis, and the object-level
proxy confirms AVX512/FMA instructions are present, but WSL lacks `perf`, so no
retired load/store/FMA attribution is available.

## Tool Matrix

| tool_or_signal | status | detail | claim_effect |
| --- | --- | --- | --- |
| cpu_avx512_flags | PASS_AVX512_EXPOSED | 11th Gen Intel(R) Core(TM) i7-11700 @ 2.50GHz | AVX512 code paths can be built/run, but this is not a performance-counter claim. |
| perf | MISSING | bash: line 15: perf: command not found perf_rc=127  | Hardware-counter-backed MAT-AVX512 optimality remains blocked if perf is missing. |
| perf_event_paranoid | RECORDED | 2 | Permission context only; perf is absent in this WSL probe. |
| objdump | AVAILABLE | /usr/bin/objdump | Assembly proxy can check expected AVX512/FMA presence, not retired counters. |
| nm | AVAILABLE | /usr/bin/nm | Symbol-level dispatch audit available. |
| build/mattrgsw.o | PRESENT | present | Object-level proxy audit can be built from current artifact. |

## Source-Level Model

| r | m_rows_outputs | repeated_scalar_complex_products | dense_mat_complex_products | dense_mat_over_repeated_scalar | generic_vector_memory_ops | mat_aware_vector_memory_ops | predicted_memory_op_reduction | source_model_vmulpd_like_ops | source_model_fma_like_ops |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2 | 3 | 8 | 9 | 1.125000 | 66 | 30 | 2.200000 | 6 | 30 |
| 4 | 5 | 16 | 25 | 1.562500 | 190 | 70 | 2.714286 | 10 | 90 |

## Assembly Proxy

| scope | instruction_lines | zmm_lines | stack_memory_reference_lines | vmulpd | vfmadd_prefix | vfmsub_prefix | vmovapd | vmovupd | note |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| mat_trgsw_mul_pvmtmlwe_DFT_from_dec_whole_dispatch_proxy | 832 | 239 | 59 | 16 | 60 | 60 | 103 | 0 | objdump proxy; static small-r helpers may be inlined into dispatch |
| mat_trgsw_mul_pvmtmlwe_DFT_public_entry_proxy | 85 | 0 | 5 | 0 | 0 | 0 | 0 | 0 | objdump proxy; static small-r helpers may be inlined into dispatch |

## Symbol / Source Guard

| check | source | status | interpretation |
| --- | --- | --- | --- |
| public_mat_ep_entry | nm | PASS | entry/symbol reference found |
| dispatch_from_dec | nm | PASS | entry/symbol reference found |
| generic_poly_mul_ref | nm | PASS | entry/symbol reference found |
| generic_poly_addmul_ref | nm | PASS | entry/symbol reference found |
| r2_smallr_source | source | PASS | r=2/r=4 source specializations are present; object symbols may be inlined |
| r4_smallr_source | source | PASS | r=2/r=4 source specializations are present; object symbols may be inlined |
| r4_unrolled_experimental_source | source | PASS | r=2/r=4 source specializations are present; object symbols may be inlined |
| smallr_dispatch_macro | source | PASS | r=2/r=4 source specializations are present; object symbols may be inlined |
| r4_unrolled_flag | source | PASS | r=2/r=4 source specializations are present; object symbols may be inlined |

## Interpretation

- The MAT-aware model predicts fewer vector memory operations than a generic
  single-poly style MAT loop: `2.200x` fewer at r=2 and `2.714x` fewer at r=4.
- That model does not make r=4 arithmetically cheap: dense MAT uses `25`
  complex products versus `16` repeated scalar products at the same simplified
  k=1,l=1 shape.
- The current object contains AVX512/FMA proxy evidence in the MAT dispatch
  region, but the static proxy cannot count retired loads/stores or prove that
  register pressure and spills are optimal.
- Therefore Stage264 is a guard against overclaiming. It narrows the next
  action to either a native perf run or a concrete code variant followed by
  full SAB `T_bootstrap/r` A/B.

## Proof Gate

| gate | status | metric | value | interpretation |
| --- | --- | --- | --- | --- |
| G1_tooling | PASS_PROXY_TOOLS | objdump/nm availability | objdump=AVAILABLE; nm=AVAILABLE | Object-level assembly proxy can be generated. |
| G2_native_perf | BLOCKED_PERF_MISSING | perf counter availability | bash: line 15: perf: command not found perf_rc=127  | No retired load/store/FMA counter claim is allowed from this environment. |
| G3_source_memory_model | PASS | predicted MAT-aware memory-op reduction | 2.200x..2.714x | The memory model supports the MAT-aware AVX hypothesis while also exposing dense r=4 arithmetic cost. |
| G4_assembly_proxy | PASS_AVX512_FMA_PROXY | zmm/FMA mnemonics in dispatch object | mat_trgsw_mul_pvmtmlwe_DFT_from_dec_whole_dispatch_proxy:zmm=239,fma=120;mat_trgsw_mul_pvmtmlwe_DFT_public_entry_proxy:zmm=0,fma=0 | Expected AVX512/FMA instructions are present, but this is not a retired-counter or optimality proof. |
| G5_symbol_source_guard | PASS | small-r source and dispatch presence | 9/9 | Stage264 audits the intended MAT external-product implementation, not an unrelated object. |
| G6_decision | PASS_STAGE264_MAT_AVX512_COUNTER_PREFLIGHT_PROXY_ONLY | stage decision | PASS_STAGE264_MAT_AVX512_COUNTER_PREFLIGHT_PROXY_ONLY | Proceed to native perf if available; otherwise use this as a claim guard and move to full-SAB A/B only for concrete variants. |

## Claim Boundary

| claim | status | allowed_wording | forbidden_wording |
| --- | --- | --- | --- |
| mat_aware_avx512_memory_model | supported_theory_model | For k=1,l=1,r=2/4, MAT-aware AVX512 register accumulation has a source-level memory-op advantage over a generic single-poly style loop. | The current MAT-AVX512 kernel has reached the theoretical optimum. |
| assembly_proxy_presence | supported_proxy | The current object contains AVX512/FMA instructions in the audited MAT external-product dispatch region. | Objdump proxy proves retired load/store behavior or absence of spills. |
| native_counter_attribution | blocked_perf_missing | Native/perf-backed MAT-AVX512 attribution remains blocked in this WSL probe because perf is missing. | Stage264 provides hardware-counter-backed load/store/FMA attribution. |
| complete_sab_speedup | not_measured_in_stage264 | Stage264 only constrains kernel-audit claims; complete SAB T_bootstrap/r speedups still come from Stage262/263 and future A/B runs. | Stage264 itself improves or proves complete SAB acceleration. |

Generated from input head `1b15115`.
