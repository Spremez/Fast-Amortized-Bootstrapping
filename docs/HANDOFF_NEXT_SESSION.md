# 交接文档（新会话入口）— 2026-09-04

> **给新会话的第一份文件。** 本文档由上一会话（已接近上下文上限）在全部工作提交后生成。深度细节见 `docs/SESSION_STATE_SNAPSHOT.md`（§十三起为近期阶段，§二十一/二十二为最近两轮）；本文件只放"继续工作所需的最小完备集"。

## 0. 项目一句话与最新叙事（2026-09-04 用户指令后）

目标：Eurocrypt 论文（独作或小团队）。**王晗（Wang Han）是本项目作者之一，同时也是 ePrint 2025/1711 的第一作者**——因此 1711 不是"他人的先行工作"，而是**本团队自己的前作**：其尺度化/矩阵外积（Mat-MGSW×Vec-MLWE、squared gadget、Δ=Q²/T 抑制）是本项目的**内层子运算**。论文叙事按两层重构：

- **内层**（源自 1711，本团队前作，如实引用+作者重叠披露）：矩阵外积 MV-EP / 尺度化 gadget（含分解优化，即我们的 SUB_DECOMP 等融合旗标所在层）。
- **外层**（本工作的设计与创新所在）：围绕内层核的**完整矩阵自举算法**——稀疏小钥匙域适配（h+1 步、间隙条件 RS 密钥、条件熵安全）、NCMUX 蝶形调度与 DualSubCMUX 双亚共享（k=2 拓扑上限证明）、r 输出尾声（packing/hw-KS）、噪声/精度域管理、CRYPTO'26 修正下的参数定案与全量实测。
- **诚实披露纪律**（用户明示保留）：1711 归属与作者重叠说明、r-lane 勘误记录（4.32 误标）、SQ p≤5@q16 适用域边界、路径A 未反超 stock 的如实声明——全部保留入文。

**安全参数标准（用户 2026-09-04 指令）：≥128 bit 即可**（不追额外余量）。

## 1. 当前定案状态

| 项 | 状态 |
|---|---|
| FINAL 参数（输入层） | n=2048: h=42/t=7/σ_in 不动，min **131.8** ≥128 ✓ 定案 |
| BSK 层决策 | **建议 A：σ_G 2⁻⁵⁰→2⁻⁴⁹**（实测近免费：+0.08 bit 噪声、门 Pass、性能零变；min 127.9→**130.4**）。用户尚未最终确认；确认后改 keygen 一行常数 + stage371 全量复跑 |
| 多环族 | 4096=h42/t8（实测 0.93-0.933，门 0/4096）；8192=h34/t10（实测 0.937，门 0/8192，推导验证）；**均已 ≥128** |
| SQ 适用域 | p≤5@q=16（p7 门 46/2048 失配=舍入地板；q=15 修复为 stage370 候选，未排） |
| 覆盖矩阵 | 全部实测闭环（stage369 A–F；见 snapshot §22.4） |

## 2. 下一阶段任务（用户 2026-09-04 指令）：外层完整矩阵自举算法的设计与创新

把矩阵外积视为内层子运算后，**外层自举算法**的设计空间与创新点（新会话的首要研究任务）：

1. **调度层**（当前：686 蝶形 per-precision-bit + DualSubCMUX k=2 共享）：候选创新——最优调度形式化（在 M3 行积定律 (1+1/r) 下求最小行积的调度）；radix>2 / mixed-radix 蝶形；跨精度位的选择子行共享（SUB_DECOMP_DFT_DIRECT 缓存的推广）；换位/直达槽比例的理论下界。
2. **密钥—形式协同**：间隙条件支撑模式与 MV-EP 计数的联合优化（(h+1)ρn 能否随支撑结构再降）；include-zero 系数处理；θ 向量 (N,h,t,r_prec,p,q,r) 在 ≥128 约束下的联合调参（现为逐环三联约束，可升级为全局优化）。
3. **尾声层**：r 输出的联合 packing（多 lane 一次 KS pass 的可能性）、样本抽取共享。
4. **噪声/精度域**：逐 lane 精度分配（混合 p）、q 的 lane 级选择（修 p7 域的更优路径 vs 全局 q=15）。
5. **理论补强**：M1/M2/M3 已立（matrix_theory_rigorous.md）；缺：调度的形式最优性、外层算法的完整伪代码级 formalization（含 7 旗标的内外层边界划分图）。
6. **安全章**：BSK 选项A 落地（若确认）→ stage371 复跑主表；组合估计器四臂记录在 snapshot §21.3–21.4。

## 3. 关键文件索引

- 理论：`docs/paper_ccf_a/sq_theory_rigorous.md`（定理1–3+1711十维对比）、`matrix_theory_rigorous.md`（M1–M3）、`theory_for_review.md`（θ向量/686基线）、`pathA_algorithm_and_differentiation.md`
- 审核包：`docs/paper_ccf_a/review_package.md` + `review_pdf/expert_review_final.pdf`（v4；v5 待用户重开：需按 M3 精化"结构1/r"表述+stage369 收官数+1711 重新定位为自有前作）
- 状态：`docs/SESSION_STATE_SNAPSHOT.md`（§21.4 BSK决策点、§22 理论补全+stage369 收官）
- 实验：`repro/stage369_coverage/`（脚本）、dell `~/spz/dell-final-bench/repro_stage369/run.log`（原始）
- 论文正文：**用户明示暂不撰写**；先完成外层设计与（可能的）stage370/371。

## 4. 机器与纪律

- **dell**（唯一实验机）：`ssh -i ~/.ssh/codex_delld_192_168_107_220 delld@192.168.107.120`，工作区 `~/spz/dell-final-bench`，负载门控 <10，keygen/探针全部环境变量化（N/OUTN/PREC/R/REPS/SIGMA_SHIFT/RPREC——加测不改码）。旧服务器实验可继续等。
- **测量纪律**：同构建内部对照唯一有效（跨构建漂移实测 −7%~−23%）；主表 6 试；门测试必过；否定性结果入册。
- **引用纪律**：1711=instantiate/adapt/prove 口径 + 作者重叠披露；Bergerat TCHES'25 未全文审（共享掩码措辞定稿前必须补审）。

## 5. 无挂起任务

stage369 六节 COMPLETE 且已收割（`7c17b7e`）；V5A2/V5A3 估计器臂完成；无本地/远程等待器。git 干净（本文件与快照更新为最后提交）。dell 上残留 2 个无害父 shell。

## 5b. 2026-09-04 第二轮用户指令（本会话执行，后续会话必须遵守）

1. **F1（MAT-EMPmul）纳入外层完整矩阵自举算法设计范围**：不考虑其原触发条件（"B/C 受阻才启动"作废）——目标是足够完备的矩阵自举算法，应做更多尝试。F1 的 δ=2 多比特选择子步即外层设计清单的 radix>2 蝶形实例；G1 有限检查器（`scripts/check_f1_empmul_equivalence.py`，160 项）可复用，G2 噪声/G3 Amdahl/G4 资源三门为立项前置义务。
2. **对比口径反转**：一切与 686 的性能对比以 **686 时间 / 我方时间** 呈现（我方为分母），直观显示快多少倍（例：SQ 5.74 ms vs 686 6.40 ms → **1.12× 更快**，不再写 0.897）。
3. **术语**：凡指 686 原实现的标量路径，直接称 **"686"**（不再用 "stock 标量"）；r-lane 语境的 "stock 构建" 改称 **"矩阵基线构建"**（matrix-base，无优化旗标的矩阵路径），避免与 686 混淆。
4. **BSK 选项 A 已落地**（用户确认 2026-09-04，commit `3d31f2f`）：probe_sq.c / probe_pvw_sq.c 默认 sigma_shift=1，main.c SET 表 sigma_out=2⁻⁴⁹；stage371 默认复跑 runner = `repro/stage371_bska_default/run_stage371.sh`（dell PID 2275197）。
5. **0904 PPT（20260904.pptx）第 3-10 页核对结论**：见 `theory_checks/stage372_ppt_0904_slides3_10_audit.md`（若已写入）——结论：第 5-9 页（流水线/MPmul/嵌套外积/bin-SAB）矩阵路径全部满足；第 8 页三变体中 ρ-SAB（一般稀疏）矩阵分支未接入（标量有 `sub_a_ga`）；第 10 页 Mul-LWE 批处理形式与 PVW_TMLWE 逐条对应满足。

## 6. 新会话开工建议顺序

1. 读本文件 → `SESSION_STATE_SNAPSHOT.md` §21–22 → 两份 rigorous 文档。
2. 与用户确认 BSK 选项A（一条消息的事，确认即改常数+排 stage371）。
3. 进入外层算法设计任务（§2 清单），先出设计文档再谈实测（用户纪律：先理论后实测、严禁猜测）。

## 6b. 2026-09-04 第三轮更新（本会话，BSK-A 已落地后的理论轮）

- BSK 选项 A 已确认并落地（`3d31f2f`），stage371 全量收官（`4c7a5ab`）；
  0904 PPT 第 3-11 页核对完毕（stage372 审计 + slide11 补遗，`bc74708`）。
- **新入口文档**（按顺序读）：
  1. `docs/paper_ccf_a/sq_position_narrative.md` —— SQ 与 G⁻¹(c)/矩阵外积
     关系的正式叙事（L3 两种核、契约抽象、四条贡献排序）；
  2. `docs/paper_ccf_a/outer_layer_design_v1.md` —— 四层架构与设计空间
     D1-D4（F1=C1、G-ρ 立项）；
  3. `docs/paper_ccf_a/outer_layer_execution_plan.md` —— **统筹执行计划**
     （闭环纪律、T2 种子推导含 radix-δ 胜利条件阶梯与 F1 投影双重计数
     修正 P-a、WS-A~F 工作流、stage373-377 排期、止损规则）。
- 下会话动作 = 计划 §4 S2：T1 formalization 定稿 + T2 定稿 + stage373
  （FINAL 参数组件画像）发出并收割。

## 6c. S3/S4 战报与一键续作（2026-09-04 晚，本会话末尾）

**已完成**（提交至 `ca2d656`）：S3 全部（G1' 检查器 232 项 0 失配双控制
检出；G2 噪声引理 +√(3/2) 界；T4 G-ρ 引理）；S4 的 F1 完整尝试**闭环为
否定性结果**（正确性门全 Pass、时序 1.38–1.58× 慢、暴露并修正 T2 种子
公式的分解共享建模错误——形式 A 无共享、形式 B 胜利条件 DFI>2(1+r)A =
r=1 +18%/r=2 持平/r=4 大负 → G3 失败，用户确认关闭，资产保留）；
**G-ρ 多体实现落地**（`sab_pvw_new_gaussian_key`/`sub_a_ga`/
`sparse_mul_gaussian`/`blind_rotate_gaussian`，正系数首门，负指数约定
核查待做）。

**下会话一键续作（G-ρ 门）**：

```bash
# 1) 推送（若本地有新改动）
scp src/sab_pvw.c src/probe_grho.c delld@192.168.107.120:~/spz/dell-final-bench/src/
scp include/sab_pvw.h delld@192.168.107.120:~/spz/dell-final-bench/include/
# 2) 构建（probe_grho 无旗标依赖；注意 setup_single_tv/sab_blind_rotate
#    需为标量公共符号，若链接报缺，在 sab.h 补声明）
ssh dell "cd ~/spz/dell-final-bench && FLAGS='-O2 -g -Isrc/mosfhet/include -Iinclude -march=native -DMOSFHET_DETERMINISTIC_RNG -DUSE_SHAKE -DUSE_SPQLIOS -DAVX512_OPT -DBINARY' && gcc \$FLAGS -c src/sab_pvw.c -o build_fin/sab_pvw_grho.o && gcc \$FLAGS -c src/probe_grho.c -o build_fin/probe_grho.o && OBJS=\$(ls build_fin/*.o | grep -v 'main\\.o' | grep -v probe_sq | grep -v probe_pvw_sq | grep -v probe_d2 | grep -v mattrgsw | grep -v 'sab_pvw' | grep -v probe_grho | tr '\\n' ' ') && gcc \$FLAGS build_fin/mattrgsw_d2.o build_fin/sab_pvw_grho.o build_fin/probe_grho.o \$OBJS -lm -o probe_grho && ./probe_grho"
```

3) 门判据：`GRHO GATE: mismatch 0 / 512 -- Pass`。过门后：负系数约定
核查（`mat_trgsw_monomial_sample` e<0 vs 标量 `RGSW_encrypt` 对照）→
负系数门 → 噪声对账（2 aut + 1 EP/系数，预测/实测<1.3）→ FINAL A/B +
钥束实测（G4-ρ：aut 族 (1+r)/2× 标量族，诚实账）。
4) 已知坑：dell 玩具 N=16 SIGSEGV（既有环境问题，N≥256 规避）；
`mod_switch_a` 在 sab_pvw.c 中调用，若未在头文件声明会隐式声明告警
（上轮 keygen 提交未编译验证——构建时注意）。

## 6d. G-ρ 门调试状态（2026-09-04 深夜，会话末尾）

**基础设施全通**：probe_grho 构建 OK（dell `probe_grho` 二进制在位），双侧盲旋转均运行，相位比较接线正确，r_prec 由完整间隙结构（含环绕间隙）推导。**首结果 FAIL：454/512 失配（~89%）**——bug 在 gaussian 机制内部。

**已排除**：编译/链接/keygen 间隙检查/mod_switch 奇性/比较接线。

**待查嫌疑（按优先级）**：
1. `pvmtmlwe_eval_automorphism` 任意 gen（≠2N−1）的语义——τ₋₁ 之外的指数从未被多体路径测过；
2. `mat_trgsw_monomial_DFT_sample(1, coeff)` vs 标量 `RGSW_encrypt(1, coeff)` 的指数约定差异（coeff∈{1,2,3}）；
3. aut_family 索引/钥生成正确性。

**首选诊断**（下会话第一个动作）：把系数全改 1 跑一次——Pass ⇒ 嫌疑 2（指数≥2），Fail ⇒ 嫌疑 1/3（ga 机制）。注意 dell 上 sed 改 `coeffs[i] = 1` 时 bumped 计数要同步（上次 sed 把计数弄坏报 "support mismatch 1"，是探针自身问题不是钥问题）。本地探针 = `src/probe_grho.c`（系数 {1,2,3} 版，已提交）；dell 的 src 副本已还原同版。

## 6e. G-ρ 调试第二轮（2026-09-05，判别实验完成）

**已定位到侧**：三方对照（PVW-gauss vs PVW-binary，同钥 coeff=1）**478/512
FAIL** → bug 在多体 `sab_pvw_sub_a_ga` 机制内部（排除：probe 标量 oracle
接线已修、指数≥2 约定、门基础设施）。coeff=1 时 sub_a_ga 数学上应退化
为 binary 的明文单项式乘（w_inv·a≡1, X^{(u·inv+1)·a}=X^{u+a}）但不等。

**剩余嫌疑（需读源码级，下会话按序查）**：
1. `polynomial_permute(out, in, gen)` 的 gen 约定（是否要求指数而非
   [0,2N) 原值；τ₋₁=2N−1 恰好两种约定一致，小奇数 gen 可能暴露差异）；
2. `pvmtmlwe_new_KS_key(key, key2, t, base)` 的方向约定与 aut_family
   钥参数（t=1/base=23 与 aut_minus1 一致——但只在 gen=2N−1 验证过）；
3. `mat_trgsw_monomial_DFT_sample` e≥1 的消息放置 vs EP 重构（e=0 已验证，
   e=1 理论上仅系数索引不同）。
4. **最有效的下一步**：写单步最小复现——trivial PVW 样本 + 单次
   `sab_pvw_sub_a_ga`（a[0]=1, X^1 选择子）vs `pvmtmlwe_mul_by_xai` 直接
   对比相位（~20 行 probe 改动，比整自举快三个数量级定位）。

本地状态：probe_grho 三方臂 + coeff_max 旋钮已提交；dell 的 probe_grho
二进制为最新（3-way 版）。
