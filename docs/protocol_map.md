# 阶段 1: 686 SAB 协议阶段图谱

目标: 把当前项目中的 sparse amortized bootstrapping (SAB) 标量路径写成后续 `sab_pvw_*` 可逐点对照的协议图谱。

核心源码:

- `include/sab.h`: `SAB_Key` 结构与 SAB API。
- `src/sparse_amortized_bootstrap.c`: keygen、blind rotation、CMUX/NCMUX、extract/packing KS。
- `src/mosfhet/src/trgsw.c`: `trgsw_mul_trlwe_DFT` 外积实现。
- `src/mosfhet/src/pvwtmlwe.c`: 当前 PVW TMLWE 半成品路径，baseline 默认未启用，不能直接作为可靠实现。

## 当前标量 SAB call graph

```text
sab_rlwe_bootstrap(out, in, tv, sab)
  sab_rlwe_bootstrap_wo_extract(tmp->rlwe_poly1, in, tv, sab)
    setup_tv_xb(...)
      setup_single_tv(...)
      builds in_N accumulators from tv and input b
    sab_blind_rotate(out_acc, in, sab)
      assert(in_k == 1)
      mod-switch input mask a
      sparse_mul(out_acc, a, a_idx=0, sab)
        for sparse key index j in [0, h)
          RGSW_monomial_mul(out_acc, sab->s[0][j], sab)
            for bit in [0, r_prec)
              for accumulator power in [0, in_N)
                CMUX or NCMUX
                  trgsw_mul_trlwe_DFT(...)
          sub_a(out_acc, a, j, sab)
            binary: monomial permutation only
            ternary: optional sign CMUX/external product
            gaussian/arbitrary: coefficient CMUX/external product
        RGSW_monomial_mul(out_acc, sab->s[0][h], sab)
  for i in [0, in_N)
    trlwe_extract_tlwe(extracted_poly[i], tmp->rlwe_poly1[i], 0)
  trlwe_full_packing_keyswitch(tmp->rlwe_in, extracted_poly, in_N, packing_key)
  trlwe_keyswitch(out, tmp->rlwe_in, hw_reducing_key)
```

## Keygen / setup map

`new_sparse_amortized_bootstrapping(...)` 当前完成:

1. 记录输入/输出维度、`h`、`r_prec`、`b_prec`、secret 类型标志。
2. 构造 automorphism key:
   - `aut_minus1` 用于 NCMUX 的 `-1` automorphism。
   - gaussian/arbitrary secret 额外构造 `aut_ksk`。
3. 构造 packing key 与 Hamming-weight reducing key:
   - `trlwe_new_full_packing_KS_key(...)`
   - `trlwe_new_KS_key(...)`
4. 为稀疏 secret selector 分配:
   - `s[in_k][h+1][r_prec]`: monomial selector bits。
   - `s_sign[in_k][h]`: ternary sign correction。
   - `s_coff[in_k][h]`: gaussian/include-zero coefficient correction。
5. 扫描 sparse input key，按 monomial gap 加密 selector bits。
6. 分配 SAB hot-path 临时对象:
   - DFT scratch: `tmp->rlwe_dft`
   - TRLWE scratch: `tmp->rlwe`, `tmp->rlwe_in`, `tmp->rlwe_poly1`, `tmp->rlwe_poly2`
   - extracted TLWE array
   - temporary TRGSW

## 当前缺口

- `copy_SAB_key` 仍是 `assert(false)`，不能安全复制 SAB key。
- `sab_blind_rotate` 明确 `assert(sab->in_k == 1)`，当前协议路径只覆盖 `in_k=1`。
- `include_zeros` 逻辑在 keygen 中仍有未实现断言；不能把 include-zero 作为当前可用 baseline。
- `pvwtmlwe.c` 当前被视为半成品，baseline 默认关闭；阶段 3 需要修复或旁路后重新实现 matrix/PVW 外积。
- 目前没有外积/CMUX/sparse_mul/sab_rlwe_bootstrap 的分层计时插桩，无法证明瓶颈归因。
- 目前没有针对 `RGSW_monomial_mul`、`sub_a`、extract/packing KS 的 deterministic 小参数测试。

## `mbfhe-mb` 中 r 的含义

在 `D:\projects\mbfhe-mb` 中，`r` 是 PVW08/multi-bit 参数:

- `src/include/lweparams.h`: `r // PVW08 parameter`
- `src/include/tlwe.h`: TLWE sample 使用 `k+r` 个 polynomial，`r` 个 body。
- `src/libtfhe/tgsw-fft-operations.cpp`: `matrixTGswFFTExternMulToTLwe(...)` 对 `k+r` 分量做分解/FFT/矩阵外积。
- `src/libtfhe/lwe-bootstrapping-functions-fft.cpp`: `tfhe_mb_MuxRotate_FFT(...)` 在相同 blind-rotation control 下更新 multi-body accumulator。

因此，本项目阶段 4 已确认采用的 `r` 不是 accumulator-index packing，而是多 body / 多 LUT / 多 SAB lane。更精确地说，它适合共享同一套 `a` 与 selector schedule 的多 lane 吞吐优化。若多个 bootstrap 的输入 mask/control 不同，不能直接当成同一 `r` batch，除非先做分组或设计额外调度。

## PVW lane 不变量

新增 `sab_pvw_*` 路径必须保持:

```text
For every CMUX/NCMUX step t and lane q:
  phase(acc_pvw.body[q] after step t)
  ==
  phase(acc_scalar[q] after the same scalar SAB step t)
```

也就是说，PVW matrix 外积可以改变数据布局和一次处理的 body 数，但不能改变 scalar SAB 的 selector schedule、monomial schedule、extract/KS 语义。

## 阶段 2 插桩目标

下一阶段需要对以下层级打点:

- `trgsw_mul_trlwe_DFT`: 直接外积 kernel 时间与次数。
- `CMUX` / `NCMUX`: 外积加 surrounding TRLWE add/sub/automorphism 的时间。
- `RGSW_monomial_mul`: bit loop 与 accumulator loop 的总时间。
- `sub_a` / `sub_a_ga`: sign/coefficient correction 成本。
- `sparse_mul`: h 个 sparse key step 加最后 monomial step。
- `sab_rlwe_bootstrap_wo_extract`: setup + blind rotation。
- `sab_rlwe_bootstrap`: extract、packing KS、HW reducing KS。

通过条件: 外积相关时间在目标参数上占主导，且 microbench 能稳定复现；否则先优化分配、转换、extract/KS 或 tmp pool。
