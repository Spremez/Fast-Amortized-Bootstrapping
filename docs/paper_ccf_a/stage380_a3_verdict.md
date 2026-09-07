# Stage380 收官：A3 数字演变定论 + M3 勘误 + 论文主表数字变更

Date: 2026-09-07（dell 实测，stage355 完全相同协议复现，6 试×双档）

## 1. 实测结果（SAB_PVW_NONBINARY_BENCH，include-zero + 全 7 旗标，
## R=4，SET_2_3_2048，同构建配对，correctness 全 Pass）

| 档 | 6 试 speedup_vs_scalar_repeated | 均值 |
|---|---|---:|
| h=39（stage355 原参数，σ_G 现为 2⁻⁴⁹） | 1.846/1.789/1.789/1.821/1.801/1.799 | **1.808×** |
| **h=42（FINAL 修正安全）** | 1.868/1.781/1.793/1.790/1.792/1.810 | **1.806×** |

（stage355 原记录 1.8217× —— 完全复现 ✓）

## 2. 三个定论

1. **stage355 的 1.8× 是真实、可复现的测量**——同机同协议 12 试确认；
   非漂移、非协议伪象。
2. **1.21× 与 1.81× 测的是不同执行路径，两者都真**：
   - 1.21× 家族 = probe_pvw_sq 的 **binary 路径**（sab_pvw_bootstrap_binary，
     7 旗标在该侧函数 0 处引用——勘误 §21.1 已证）；矩阵基线 10.7 s/lane。
   - 1.81× 家族 = main.c 的 **include-zero 路径 + 全旗标**（旗标真实生效，
     PVW 7.13 s/lane；SUBA_INCLUDE_ZERO_COEFF_ONE_FAST 即该路径专用）。
   差异 1.5× = 旗标在生效路径上的真实收益。
3. **安全修正免费**（include-zero harness 下 1.808→1.806）——因为标量
   基线同受 h 影响，比值不变。

## 3. 论文主表数字变更（按用户规则：以事实最优为准）

- **主数字 = 1.81×（r=4，FINAL h=42，include-zero 全系统，同构建配对，
  门全 Pass）**——这是完整系统的真实吞吐。
- 1.21× 保留为 binary 路径口径（副表/附录），两口径差异（旗标作用面）
  如实解释。
- 修正安全下的完整对比（同口径）：686×r 1.81×、TFHE-rs 满占用 1.91×、
  BatchBoot 全集 <128（stage381）。

## 4. M3 勘误（matrix_theory_rigorous.md §四，理论侧同步修正）

原文行账错误：把标量每输出的行数记为 ℓ（漏 (k+1) 因子）。正确账：

```text
标量 r lane：每事件 r·(k+1)·ℓ 行；每输出 2ℓ 行（k=1）
矩阵：每事件 (1+r)·ℓ 行；每输出 (1+r)ℓ/r = 1.25ℓ 行
行工作上限 = 2(k+1)r/(1+r)·(1/ℓ)·ℓ …  k=1,r=4: 2·4/5 = 1.6×
```

- **行粒度结构上限从"1.25×"修正为 2(k+1)r/(1+r)（r=4 时 1.6×）**。
- 实测总时 1.81× 超出行上限 1.6× 的部分 = 旗标消除的非行开销
  （分解通道/拷贝/bookkeeping，stage373 画像中非 addmul 占 ~50%）+
  选择子行读取摊销——与 stage373 分量账自洽。
- 影响追溯：T2/F1 判定使用的是 D/F/I/A 相对量与修正胜利条件，不受
  基线因子影响（比值形式不变）；但引用"1.25× 上限"的段落（含
  matrix_theory_rigorous §四、执行计划、与用户的沟通记录）全部按本
  勘误更正。

## 5. 演变对照表 A 行判定（number_evolution_reconciliation.md）

A 行（stage355 1.83× 家族）判定为 **"真实测量、协议有效、参数档标注后
可作为主表数字来源"**——差距全部由执行路径差异解释（第 2 节），无任何
漂移/伪象成分。D/E 行随本判定同步收敛。

## 6. 过程注记

- 复现过程中修复两个真 bug（均已在树内）：free_sab_pvw_key 的 s_coff
  double-free、nonbinary keygen 缺 aut_family/gaussian_secret NULL 初始化
  ——两者导致本 harness 缓冲输出在退出时丢失（曾误读为"无输出"）。
- 原始日志：dell `repro_stage380/run.log` + 12 个 run 日志；runner：
  `repro/stage380_a3_rerun/run_stage380.sh`。
