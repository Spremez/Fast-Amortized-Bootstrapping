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

## 6f. G-ρ 收官（2026-09-07，正确性+噪声全闭合）

**全部正确性门 Pass（dell，N=256/out1024/h=6/r=2，标量 oracle = 规范
`sab_rlwe_bootstrap_wo_extract`）**：
- coeff=1（退化为 binary 语义）：**0/512 Pass**
- 正系数 {1,2,3}（ρ≥3 一般稀疏）：**0/512 Pass**
- 负系数 {1,−1,2,−2,3,−3}（签名循环，同一 monomial 折叠约定）：**0/512 Pass**
- 链级隔离 CHAINTEST（gaussian 调度 vs 手工蝶形+奇 a 单项式链）：0/512 OK
- 单步 STEPFEST（均匀+多样 a）：全 OK
- **噪声对账**：pair max dev log2 = 53.10（正）/ 53.14（负）≪ 预算 60，
  与标量同阶 —— T4 预测实测确认（<1.3 门过）。

**调试史教训（入册）**：三轮"失败"全部是 probe 参照系 bug（盲旋转未在
setup 数组原位执行；遗留 `setup_single_tv` 偏移公式 1/(2·b_prec) ≠ 规范
1/(2·2^b_prec)；参考链 `pvmtmlwe_mul_by_xai` 原位别名——该函数不支持
out==in）。**实现自身自首个提交（ca2d656）起正确**。另：`pvmtmlwe_mul_by_xai`
与 `pvmtmlwe_from_DFT_add`（非融合分支）均有 out==in 别名限制——已列入
代码坑清单，供后续内核工作参考。

**剩余（stage378，待排）**：FINAL（h=42/N=2048）A/B 时序 + **全钥束实测**
（G4-ρ 诚实账：aut 族 = 2048 把多体自同构钥 ≈ (1+r)/2× 标量族，keygen
时间需实测；此前不作小钥声明）。probe 的 N/h env 化 + stage378 脚本。

## 6g. 完整算法目标达成（2026-09-07，本会话终局）

**"验证过的正确完整算法 + 理论支撑 + 优势数据"三项全部闭合**：
- 正确性：binary 全域 + SQ 全量 + G-ρ 全域（FINAL 0/4096）+ δ=2 机制
  （门全 Pass，作为否定性结果关闭）——外层所有已实现路径均过 oracle 等价；
- 理论：T1 形式化、T2 修正模型（行模型 FINAL 校准精确）、M1-M3、
  G1'/G2/T4、SQ 定理 1-3 + 统一族 q* 规则、叙事三层（sq_position/
  outer_layer_design/outer_algorithm_formalization）；
- 数据：686/SQ = 1.117× 标量、686×r 1.21× r-lane（binary）、安全 min
  130.4 ≥128 定案（stage371 全量收官）、G-ρ 资源/代价诚实账、
  F1/C5 两个否定性闭环 + T2 勘误（方法论资产）。
- 剩余 = 纯论文侧：dossier v5（M3 精化 + 1711 重新定位 + G-ρ 新章 +
  stage369-379 数据刷新 + 新口径表 686/我方）；Bergerat TCHES'25 补审；
  可选 stage370（q15）。

## 6h. Top-5 执行轮战报（2026-09-07，本会话）

**① BatchBoot 重评（stage381，e69c21f）**：其四个主参数集在修正口径下
**全部 FAIL <128**（124.2/124.2/120.5/124.6；BSK 层判据来自标准新
lattice-estimator，独立于我们的 T3' 方法）。论文主张解锁："修正安全下
唯一 ≥128 的摊销自举实现 = 本工作（130.4）"。

**② A3 数字演变定论（stage380，0cd2701）**：stage355 的 1.8× 完全复现
（h=39 六试均值 1.808×；**h=42 FINAL 六试均值 1.806×，安全修正免费**）。
1.81× 与 1.21× 测的是不同执行路径（include-zero 全旗标侧 vs binary
无旗标侧），两者都真。**论文主表数字 = 1.81×**。附带 **M3 勘误**：
行工作上限修正为 2(k+1)r/(1+r)=1.6×（原 1.25× 漏 (k+1) 因子），
1.81× 的超限部分 = 旗标消除的非行开销（与 stage373 分量账自洽）。

**③ 历史数字矛盾全面处置**：演变对照表十家族定稿
（number_evolution_reconciliation.md）；review_package 幽灵数字 1.48×
清除 + §〇 过时清单标注；过程中修复两个真 bug（free 路径 s_coff
double-free、nonbinary keygen aut_family 未初始化）。

**修订后的论文主张（数据基座）**：修正安全（≥128，唯一达标）+
1.81× 全系统吞吐（同构建配对，安全修正免费）+ 密钥 ≤1.07× Pareto +
G-ρ 语义完备 + 完整理论链（定理 1-3、M1-M3 勘误后、T4）+ 三组否定性
结果。评审 agent 的 A1/A3 攻击点已被本轮数据实质削弱；Top-5 剩余
（证明升格、第二平台、DFR certified、v5 单源化）照旧。

## 6i. 终极任务：r-Input Batching + Hom-Tr 完整实现 + 论文撰写（2026-09-08 用户最终指令）

**用户决策**：r-input batching 是论文必须项（"Combining Packing and Batching"
标题要求）；数学与算法部分必须达到世界最顶尖审稿人标准。

### 必须完成的数学工作（投稿级）

| # | 内容 | 当前状态 | Eurocrypt 要求 |
|---|---|---|---|
| M-HT.1 | 交织打包的形式化定义（N=r·d, Y=X^r, 环扩张 R/A） | Agent 参考变体 | 完整定义 + 与 body-packing 的等价性证明 |
| M-HT.2 | 固定子群 H 的迹算子 T_H 的性质 | Agent 推导 | 完整证明（线性性、提取公式、与 H 的关系） |
| M-HT.3 | Hom-Tr 的正确性（per-lane 相位不变式） | **未证明** | 完整归纳证明（逐步骤：蝶形 + Hom-Tr 交替） |
| M-HT.4 | Hom-Tr 的噪声分析 | **未推导** | 次高斯参数界（aut-KS + 公开权重乘 + 舍入 + 模数消耗） |
| M-HT.5 | 模数消耗的严格分析 | Agent 方案（方案 C） | 证明每步消耗 log₂(r) bit 的下界 + 最终精度 |
| M-HT.6 | 与 r-LUT batching 的正交性证明 | 定性论证 | 形式化证明两个维度可独立组合 |
| M-HT.7 | 总复杂度分析 | 未做 | 结合两个维度的完整复杂度 |
| M-HT.8 | GF(257) 机械验证 | 未做 | 交织打包 + 迹提取 + Hom-Tr 的机器检查 |

### 必须完成的实现工作

| # | 组件 | 依赖 |
|---|---|---|
| I-1 | 交织打包/解包（body ↔ interleaved 转换） | M-HT.1 |
| I-2 | 迹操作 T_H（复用 aut_family） | M-HT.2 |
| I-3 | 权重多项式 P_w 计算 | M-HT.2 |
| I-4 | 尺度管理（q 位跟踪 + 右移 + 舍入） | M-HT.5 |
| I-5 | Hom-Tr 版 sub_a | M-HT.3 |
| I-6 | multi-input setup + bootstrap wrapper | I-1..I-5 |
| I-7 | 正确性门（vs r 个独立标量 oracle） | I-6 |
| I-8 | 噪声对账 + benchmark | M-HT.4 + I-7 |

### 建议路径

r=2 先行（模数消耗 42 bit 在 64-bit 内），验证后扩展 r=4（需 128-bit
中间精度或周期性降尺度）。预估 5-7 个专注会话。

### 新会话入口文件

1. `docs/HANDOFF_NEXT_SESSION.md`（本文件，含全部历史决策）
2. `docs/paper_ccf_a/unified_status_document.md`（当前状态 + 待对齐）
3. `theory_checks/stage395_rinput_implementation_plan.md`（实现计划）
4. `theory_checks/stage391_homtr_agent_correction.md`（agent 数学推导）
5. Wang Han `20260908V1.pdf`（理论草稿）
6. 独立 agent 分析（`HomTr_WangHan_Fusion_Analysis.md`，258 行）

## 6j. r-Input Batching + Hom-Tr 执行战报（2026-09-08 本会话）

**已完成（提交见 git log）**：
1. **数学（M-HT.1-6，theory_checks/stage396_rinput_homtr_math.md）**：
   HT-1/HT-2 迹提取与 U_a 恒等式（含一般嵌入偏移形式）；**换位扭曲
   否定性结果**（HT-4'：任何预因子/单自同构都无法修复 σ₋₁ 对 lane 1
   的奇数次 Y-扭曲——奇偶性障碍）；**Ψ 微修正**（HT-4：
   Ψ = U_{(0,1)}∘σ₋₁ 使换位作用 lane 一致，第二自同构与 sub_a 共钥）；
   HT-5 提升定理；**伪差抵消定理 HT-7'**（±迹权重使 ±2^63 重缩放伪差
   在下一 U_a 处 mod 2^64 严格消失）与**终恒等倍增协议 HT-8**（全
   重缩放 + 末尾 ×2 + 抽取端 ÷2——2-幂 torus 上封闭，替代旧
   h·log₂r 模数账目，HT-9 记旧模型出处并证其噪声指数放大不可行）。
2. **GF(257) 机械验证（M-HT.7-8，scripts/check_rinput_homtr_gf257.py）
   ALL PASS**：C1-C6 + C4 决定性（Ψ 修正交织管线 vs 2 独立输入标量
   oracle：2560/2560 全等）+ 负对照（裸 σ₋₁：1280/2560 失配=lane 1
   全部——扭曲存在的机械证据）。
3. **C 实现（I-1..I-6）**：include/sab_rinput.h + src/sab_rinput.c
   （keygen/交织 setup/Ψ/Hom-Tr sub_a/蝶形/盲旋转含终倍增）；
   probe_rinput.c（G0 setup 门本地 Pass + oracle 门 + min_oracle_key）；
   probe_rinput_diag.c（逐阶段锁步：**交织实现 vs 明文模型全阶段
   噪声级一致**，setup 精确）；probe_cmux_dims.c（维度隔离）。
4. **本地构建负结果（入册 §10.2）**：dim=512 TRLWE 外积本地损坏
   （裸 CMUX dev 2^63；256/1024 正常）；确定性 RNG 间歇失效；
   packing KS 构造本地部分维度段错误。I-7 初败 477/512 的根因即
   oracle 用了 d=512。

**未闭合（下会话入口）**：
- **I-7 门 163-188/512 波动**（lane0 ~60/lane1 ~110，稀疏槽位 X，
  pair dev 2^63 类；经 4 轮修复自 477 递减）。关键定位事实：
  (a) 交织 C vs 明文模型逐阶段噪声级一致（diag@2048，setup 精确）；
  (b) 我的标量模型 vs oracle 逐阶段噪声级一致（d=1024，setup 精确，
  probe_scalar_model）；(c) GF(257) 两模型精确等价——但 diag 的比较
  掩掉 bit63，三方"传递"对 ±2^63 类是盲的。稀疏失败槽 + 2^63 幅度
  指向伪差抵消定理（HT-7'）某假设在特定数据流下不满足（候选：终
  蝶形直达槽与 Ψ 槽的交互、或 oracle 侧 dim-1024 亦有本地污染）。
  优先：(a) dell 同构建跑 probe_rinput（本地三缺陷均 MinGW 特有）；
  (b) 若仍败，把 probe_rinput_diag 的 stage_dev_masked 换成全值比较
  （去掩码）在 dell 逐阶段定位首个 2^63 出现阶段。
- **I-8**：过门后噪声对账（M-HT.4 标定）+ benchmark（本地参考：
  interleaved ≈ 1.33-1.6× of 2×scalar@toy，不可入论文）。
- 论文侧：stage396 数学全文入 §3.4/新 §3.7；Ψ/HT-7'/HT-8 为本工作
  独立贡献（Wang Han 草稿未含），与 8 问一并发 Wang Han。

## 6k. V2 草稿分析定案（2026-09-09，stage397）

用户指令：完成 20260908V2 的 Alg3/Alg4；自举渐进复杂度需优于 686。
**入口文档：theory_checks/stage397_v2_alg34_gap_analysis.md**（全文分析+
工作计划+给 Wang Han 的 8 问 V2 版）。三条定论：

1. **Alg3/Alg4 = 我们已验证的矩阵路径**（Vec-MLWE=PVW_TMLWE、对角
   Mat-MGSW=MAT_TRGSW、⊡=mat EP）；草稿 Alg4 行 9（明文 c_k·X^{a_k}）
   对 r 个不同输入**数学错误**（stage395 障碍），须换我们的 U_a 相对迹
   sub_a（stage396 HT-2'，GF(257) 2560/2560）。
2. **渐近复杂度定论**：类内（加密选择子盲旋转）每消息成本
   (h+1)ρℓNlogN·(行常数)，N≥n/2 为类约束；686 常数 = k+1 = 2，我们
   = 1+k/r → 1（r→∞）——**类内无超常数分离，主张必须写"匹配下界的
   渐近最优 + 常数 (k+1) 优势"**；下界定理（M-V2.5）= 欧密级新贡献。
3. **关键路径**：M-V2.5（下界/最优性定理，1.5 会话）+ I-V2.6（r-input
   dell 门，1 会话）+ M-V2.1/2/3/4（Alg3/4 定稿+证明+噪声主定理，3
   会话）+ W-V2.8（论文组装，2 会话）≈ 7.5 会话达投稿。

## 6l. 接手 Wang Han 贡献：Alg1/2 完成 + ρ 消去调查定案（2026-09-09，stage398）

用户指令：接手 Alg1/2 理论与设计（combined packing and batching），
需渐近复杂度优势。**入口：theory_checks/stage398_osmpmul_and_alg12_completion.md**。
定案四条：

1. **语义分解定理 S1（机器证实 M0 240/240）**：蝶形移动 ⟺ 纯重标 +
   跨界内容条件 σ₋₁；间隙指数不进入相位（间隙=行选择器，跨界符号=
   负循环行符号）。检查器 check_osmpmul_gf257.py（M0 过 / M1 单发
   单项式假设 REFUTED 240 失配 / M2 对照失配）。
2. **不可能性 S2-S4**：秘密置换 ⟹ ρ 不可消去（类时间下界闭合）；
   时间-密钥权衡曲线通用（对 686 同样可用，非分离轴）；N 自由度
   分组分析对称。**超常数时间渐近优势在本类被证明不存在。**
3. **Alg 1'/2' 完成版**（草稿行 9 错误已替换为 U_a 相对迹；Ψ 换位
   修正；终倍增协议）——全链 GF(257) 2560/2560（stage396 C4）。
4. **可证渐近主张定稿（A2/A3）**：每消息 T(r) = (h+1)ρℓNlogN(1+k/r)
   = **批处理轴 Θ(1/r) 渐近**，r→∞ → 1/(k+1)（k=1: 2×），下界匹配
   定数 1（686 为 k+1）。论文复杂度章 = "渐近最优 + 最优常数 +
   多项式噪声 + 修正安全唯一"。

## 6m. 下界论证完备性定案（2026-09-09，stage399）

用户问：下界是否可受顶级审查？成立条件？入口：
**theory_checks/stage399_lower_bound_formalization.md**。定案：
1. **形态**：模型 C0 内定理（非猜想、非仅对 686——686/TFHE/FHEW/
   BatchBoot/本工作均为类成员），四条件显式（H1 单项式累积范式 /
   H2 密钥束 poly(λ,log n) / H3 代价模型双口径 / H4 gap 密钥结构）；
   类普适性=开放问题（如实标注，附循环依赖论证）。
2. **自我攻击发现并修补**：大环混合构造 HYB（单发单项式 Z^{v_t}
   移动 + 抽取/扭转/packing-KS 重打包）可在密钥 ∝ n 时消去 ρ——
   已作为时间-密钥前沿 LB-F 的中间匹配点写入（HYB 违反 H2；实用
   域 ρ<12 恒慢，渐近域快 Θ(ρ)）；主定理升级为乘积形式
   T·K = Ω(...)，三个匹配点（蝶形/HYB/per-行选择子）。
3. **"达理论下界"的准确主张**：标准密钥束制式（H2，与 686 同预算
   可比）下匹配下界且行常数最优 (1+k/r)→1；主张措辞已给定。
4. 剩余纯数学义务 OB-1..6（≈2.5-3 会话）：L2' 影响度完整引理、
   五族类成员解释、S3'/LB-F 成稿、HYB 小参数验证 + crossover
   标定。无实验依赖（I-7 dell 门另行并行）。

## 6n. PI 计划 + OB-1 执行（2026-09-09，stage400/401）

用户指令：agent 任投稿 PI，全面规划并逐项执行；理论与实验双严。
**stage400 = 总体作战计划（单一事实源）**：C1-C4 贡献定稿、记号统一
表、四工作流义务清单（WS-A 纯数学 5S / WS-B 实验 4S / WS-C 论文
3.5S / WS-D 协作合规 1.75S，关键路径与风险表）、顶级审查特别防线
（定理四件套模板、否定性结果目录、GF(257) 工件化、统计口径、回应
信预置）。**stage401 = OB-1 完成**：L2 三层完整证明——
(i) 无条件弱式（触碰 n 门 + 像集-锥 2^ρ−1，任意 DAG）；
(ii) 层式宽度 n 强式 n·Θ(ρ)/相位（可达性倍增归纳 + 模型忠实性引理
3.0 逐一核对 686/TFHE/本工作实现）；
(iii) 一般 DAG 开放（如实注记）。
自我勘误四项入册：影响度路线废弃（像集归纳更干净）；新增 H5 均匀性
假设（否则硬连线零门反例）；元数限制=密钥预算引理（非精度——单项式
消息范数恒 1）；(h+1) 因子显式绑定 H1（引理 L4，循环依赖论证）。
下会话执行序：OB-2（五族类成员）+ OB-3（LB-F 成稿）；并行发 I-1
（dell r-input 门）。

## 6o. PI 执行轮战报（2026-09-09 晚，stage402 + I-1 深挖）

**OB-2 完成**：stage402_class_membership.md —— 五族（686/TFHE/FHEW/
BatchBoot/本工作）C0 类成员解释引理 + 覆盖定理 CM + 诚实边界注记。

**I-1 dell 判定执行**（真 bug 确认 + 三层定位到最后一层）：
1. dell 构建/运行 OK；门失败 176/512（同本地）——**排除本地缺陷假设**。
2. 逐步诊断：setup 精确 0；终倍增后 C↔模型 dev 55.64（噪声级）——
   C 实现正确跟踪其模型。
3. probe_scalar_model 强制门间隙 [30,57,36,24,18,5,86]：stock oracle
   ↔ 标量模型全阶段 ≤48.3、min↔stock 0 失配——**oracle 侧正确**。
4. GF(257) 在门形状（N=2048/d=1024/n=256/h=6/rp=7/同间隙表）随机数据
   全等 524288/524288——**语义在该形状正确**（scripts/repro_gate_shape_gf257.py）。
5. **门在诊断器内复现**（GATE-REPLICA 130/256，同签名 sc/int 差
   ≈8-9 个 LUT 级）——关键裁决：**exp（明文交织模型）量化值 == C
   密文（int0==exp）但 ≠ oracle**：模型携带非-2^63-纯类差异
   （差 ~1.25·2^63 = 10·2^60）。
6. **最后一层定位**：我的 python 重放模型（replay_gate_data.py，用
   导出的精确 uint64 数据）与标量模型 mod-2^63 全阶段一致；而诊断器
   的 C 模型与 oracle 差 10·2^60 ⟹ **python 模型 ≠ 诊断器 C 模型**
   （同为"相同公式"的两个转录存在分歧）——下一会话第一动作：
   逐阶段 diff 导出的 exp vs 重放 acc_i，找到分叉阶段与系数。
   **首要嫌疑**：mod-switch 的 uint64 舍入边界（torus2int 的 +off 溢出/
   舍入方向）被 GF(257) 抽象掩盖；或 psi/suba 的指数取模次序差异。
   工件：repro/rinput_gate_data.txt（精确数据）、scripts/replay_gate_data.py
   （重放+掩码比较）、诊断器内 GATE-REPLICA + 数据导出。

**修复后即达 I-7 门**（其余全部就绪：oracle/实现/语义三侧单独验证过）。

## 6p. 🚀 I-7 门闭合（2026-09-09 深夜，dell：mismatch 0/512 PASS）

**根因**（完整证据链）：终倍增协议 HT-8 的伪差抵消要求**带符号**不回绕：
|2μ| < 2^64 ⟹ **|μ| < 2^62（两位守卫）**。实现误用一位守卫（TV 量化
v·2^(63-p)，最大 0.875·2^63 > 2^62），终倍增 2μ 回绕 2^64，抽取值
偏移恰好 2^63/2^(62-p) = 2^(p+1) 格 LUT —— 与观测（v_int 与 v_scalar
差 8-9 格、51% 系数、C/py/C-oracle 三方各自内部自洽）逐点吻合。
定位路径：oracle 全量导出（修正我自己的无符号比较 bug——差值实为
-2^45 噪声级，oracle≡py 标量镜像）→ 单脚本逐阶段 masked 对拍
（setup/bfly0-6/suba0-5 全 0，最后在终倍增语义处暴露）→ 手算 slot 1
（scalar=-7·2^60 与 model_i=+2^60 差恰 2^63，倍增后 2·scalar 回绕）。

**修复**：TV 量化 v·2^(62-p)（两位守卫，即 stage396 §5.3 推论的正确
形式），抽取口径匹配（scalar >> (62-p)，interleaved >> (62-p+1)）。
**门结果（dell，同构建配对）**：G0 setup 0 失配 ✓；**RINPUT GATE
mismatch 0/512（lane0 0, lane1 0）PASS**；pair 噪声 2^53.76 ≪ 预算
（I-8 噪声对账的初值）；计时 interleaved 317ms vs 2×scalar 227ms
（ratio 1.39×，玩具参数）。

**连带修正义务**：(a) stage396 HT-8 措辞统一为两位守卫（§5.3 推论
正确，§3.1 残留一位表述需改）；(b) 论文 Alg 2' 的 TV 量化与抽取公式
按此口径；(c) I-2/I-3（噪声对账+benchmark）现在可执行。

**门稳定性与第二参数点（同日补测）**：3 次重复全 PASS（0/512，
噪声 2^53.76 稳定）；第二参数点 in_N=512/h=8/r_prec=9：**0/1024
PASS**，噪声 2^54.21。I-7 在两个参数点 × 重复运行下闭合。

## 6q. I-2/I-3 闭合（2026-09-09 夜，66f15b2）

probe_rinput 升级为 6 试驱动 + 三路噪声标定（σ_s 网格残差 / σ_KS
满熵 LCG mask 单次自同构 / σ_EP 合成随机 mask 单次 CMUX）+ M-HT.4
括号对账。**两个参数点各 6 试门全 PASS**：

| 点 | 门 | pair rms | median ratio | 对账括号 |
|---|---|---|---|---|
| n=256/h=6/rp=7 | 6/6 (0/512) | 2^53.99 | **1.35-1.40×** | [2^46.75, 2^63.94] ∋ 实测 |
| n=512/h=8/rp=9 | 6/6 (0/1024) | 2^54.30 | **1.440×** | [2^46.x, 2^64.29] ∋ 实测 |

标定修 bug 记录：零 mask → KS 误差恒 0（分解残差来自 mask 低 41 位）；
p2 相位缓冲自覆盖。紧 (<1.3) 对账 = M-A3 逐步 profiler 义务（噪声主
定理章的仪器）。结果表：repro/stage403_rinput_bench/RESULTS.md。
dell 链接备忘：需 -Wl,--allow-multiple-definition + 尾置 spqlios-ifft。

**stage400 进度**：OB-1 ✓ OB-2 ✓ I-1 ✓ I-2 ✓ I-3 ✓（5/22）。
下一优先：OB-3（LB-F 前沿成稿，0.5S）+ M-A1（Alg1'/2' 论文章）。

## 6r. 用户常设计律（2026-09-09 终局指令，所有后续会话必须遵守）

> "实验作为佐证是可以的，也需要严格的理论分析以及噪声分析等等
> 同态理论研究所关注的都要严谨且完备考虑进去，由算法理论出发到
> 形式化证明与分析再到实验验证都是需要的，中间不能存在猜测的行为。"

**执行标准（写死）**：
1. **链式完备**：每个主张必须走完 算法理论（构造+直觉）→ 形式化
   （定理/引理，显式假设编号）→ 证明（无"显然"、无跳步；归纳写全）
   → 机器佐证（GF(257)/机械验证，如适用）→ 实测（同构建配对、
   重复、溯源）。**任何一环缺失 = 该主张不得入论文正文**。
2. **噪声分析完备**（同态理论关注面清单）：正确性（消息路径逐系数
   精确性）、噪声增长（次高斯参数递推、Pythagorean 合成、最坏/平均
   双口径）、精度/模数预算（守卫位、mod-switch 舍入）、密钥束尺寸、
   安全参数耦合。M-A3（噪声主定理 + 逐步 profiler 紧对账 <1.3）按
   本纪律**升为最高优先**。
3. **零猜测**：开放问题如实标注（已有先例：DAG 强形式开放、类普适
   性开放）；不得以"预期/应当"替代证明；负结果照录。
4. **当前不满足项**（诚实清单，须补齐）：I-2 紧对账（现为括号
   [2^46.75, 2^63.94]∋实测，非 <1.3）→ M-A3 逐步 profiler；
   M-HT.4 的 EP 项完整推导（现为实测标定）；HYB 噪声账的引理化
   （stage404 §2.3 现为注记，需并入 M-A3 形式化）。

## 6s. OB-3 闭合（2026-09-09 终局，stage404）

LB-F 前沿定理定稿：**弃用 stage399 §7.2 乘积式**（量纲自勘误），
改三制式形式（F1 标准钥/下界匹配+行常数最优；F2 线性钥/HYB 见证/
crossover ρ*≈11 严格计算；F3 平方钥/信息地板），含 HYB 完整成本账
（c_ks≈9 标定自尾声实测）、噪声注记、论文 §5.3 底稿段落、六件
一致性自检。**stage400 进度 6/22**（OB-1/2/3、I-1/2/3 完成）。
下一优先（按 6r 纪律）：**M-A3（噪声主定理+逐步 profiler，含 I-2
紧对账收口）→ M-A1（Alg 1'/2' 论文章）→ M-A2/M-A4 → P-1..5。**

## 6t. M-A3 闭合（2026-09-09 深夜，stage405）：噪声主定理 N1 + 逐步 profiler 紧对账 + 两个标定 bug 勘误

**入口文件**：`theory_checks/stage405_noise_master_theorem.md`（N1 全文）
+ `repro/stage405_rinput_prof/RESULTS.md`（对表）+ `src/probe_rinput_prof.c`
（仪器；MICRO 判别模式 SAB_RINPUT_MICRO=1、AES 操作数模式
SAB_RINPUT_AES=1）。**I-2 紧对账收口**：两参数点 × 6 试逐阶段
worst |lr| = 0.171/0.186、FINAL −0.01/−0.00、PAIR +0.28/+0.24，
全部 <1.3× 门 ALL PASS（旧括号 [2^46.75, 2^63.94] 作废）。

**机制链（全部机器裁决，零猜测；细节见 stage405 §0-§3）**：
1. **两种数位化约定**（代码锚定）：EP 侧 pvmtmlwe_decompose
   （offset 2^63）残差**单边** U[0,2^41)（μ_ε=2^40）；KS 侧
   polynomial_decompose_i（offset 2^63+2^40 半数位）残差**平衡**。
2. **N-EP 恒等式**（精确整数裁决 max dev=0）：φ_EP = dec(D.a)⊗e_0 +
   dec(D.b)⊗e_1 + m·(ε_a⊗s − ε_b) + ν_DFT。
3. **N-DC 游走定理（本会话核心发现）**：E[ε_a⊗s] = μ_ε·(2H(i)−hw)
   单调阶梯，rms = μ_ε·N/√12 = **2^49.20**（实测 49.18-49.21）；
   只依赖密钥 ⇒ m=1 事件的 DC 图样**相干线性累积**（实测 4 事件
   = 精确 4×），跨相位被 U_a 移位部分去相关。DC 轨 = 确定性整数
   算术可精确预测；白轨 = 事件计数二次累积。
4. 原语七元组闭式 vs 实测全部 ≤0.3 bit（表见 stage405 §0）。
5. **奇尾现象**（如实注记 open）：lane-1 尾列 2^57-61.8 级偏差 =
   fold-alias 于无守卫不变式列的 ≥2^63 伪差类；对抽取通道/门/pair/
   GF(257) 零影响；完整逐列代数留作后续形式化。
6. **勘误入册**：stage403 上界模型合成 EP 标定把消息差当噪声；
   stage396 §4 旧噪声形式（缺 EP/DC 项 + 不存在的 2^126/12 舍入项）
   由 HT-6' 取代（两文件已加勘误头）。
7. **实现级优化候选（记录未实施）**：EP 数位化加半数位偏移即消
   μ_ε ⇒ 每 m=1 EP 噪声 2^49.2→~2^44.5（−4.7 bit）。
8. N-S（尺度化 gadget 统一 = Wang Han Lemma 1.7 形式 → Thm 2
   2^{q+3.7} ±0.2 bit）与 N-HYB（HYB 噪声账引理化）已成文。

**stage400 进度 7/22**（OB-1/2/3、I-1/2/3、**M-A3**）。
**下一优先：M-A1（Alg 1'/2' 论文章）→ M-A4（HT-10 正交组合）→
M-A2 → OB-4 → P-2 装配（N1/N-S 素材已就绪）→ I-6（FINAL 参数
profiler 复核 + σ_kg 重标定）。**

## 6u. WS-A 全部完成（2026-09-09 续会话，stage406-409）：四个论文章级交付物

**M-A1（stage406）= 论文 §3 章投稿级全文**：Alg 1'（Ψ 修正换位蝶形）
+ Alg 2'（U_a 相对迹替换草稿行 9 + 终倍增协议）；正确性定理 C1'
（HT-5+M1+S1 组合，逐步归纳无跳步）；GF(257) 对应关系表（C4 决定性
2560/2560 + 三件负对照）；**与 V2 草稿差异逐行表（D-1 发送素材）**
定位三处修正 F-i/F-ii/F-iii；sub_a 四后端设计空间表。

**M-A4（stage407）= HT-10 正交组合定理**：(S) 语义逐通道不变式
（HT-5 归纳 × M1 体对角；环作用与体作用交换为正交根源）、(C) 成本
相加 + 摊销常数 r=r₁r₂ 合成、(N) 逐通道噪声递推；联合实例如实记为
未实现（I-5 可选门 = GF(257) body 维扩展，0.5 会话）。

**M-A2（stage408）= 换位扭曲吸收否定性定理 Ψ-Nec**：对角 Mat-MGSW
选择子不可吸收 σ₋₁ 的 lane 扭曲（两行反证：乘法算子与 Y-平移交换、
J 反交换）；推论 Ψ-Min（Ψ 是最小钥成本修正，全管线恰两把 aut 钥）；
与 HT-4' 分工（明文层 vs 密文层修复穷尽）。

**OB-4（stage409）= 论文 §5 章投稿级全文**：双口径 M_lin/M_fft；
三层每相位下界（弱式无条件/强式层式/DAG 开放如实）+ 元数-钥预算
引理 + L4 相位独立性；LB-F 三制式前沿（F1 匹配+行常数最优、F2 HYB
crossover ρ*≈11、F3 信息地板）；A1-A3 摊销定律；CM 五族覆盖；否定
性结果目录；**11/11 一致性 diff 通过**。

**stage400 进度 11/22：WS-A 完成 8/8（OB-1..4 + M-A1..A4）**；
WS-B I-1/2/3 完成（I-4 部分：c_ks≈9 已从尾声实测标定入 stage404）。
**下一优先：WS-C 装配 P-2（§3-5：stage406=§3、stage405=§4、
stage409=§5 全部就绪）与 P-1（§1-2 intro+prelim，升级
paper_full_v1.md）→ P-3（§6-7 安全+实验）→ P-4（附录 B/C/D）→
P-5（记号 lint）→ D-1（8 问 + stage406 §3.7 差异表发 Wang Han）。
并行可选：I-5（r₁⊗r₂ 玩具门）、I-6（FINAL 参数 profiler + σ_kg
重标定）。**

## 6v. P-1/P-2 + D-1 包（2026-09-09 同会话续）

- **paper_full_v2.md**（P-1/P-2）：新标题（信息论前沿框架）、
  abstract 草、四贡献 C1-C4 定稿结构、§1 含 1711 内层原语定位 +
  作者重叠披露、§2 记号表（stage400 单一来源）、§3-5 以单一事实源
  指针汇入（stage406/405/409）、§6-8 与附录为 P-3/P-4 存根。
- **d1_wanghan_package.md**（D-1 就绪，待用户转发）：8 问 V2 +
  三修正件差异表（F-i Ψ/F-ii 行 9 U_a/F-iii 终倍增）+ D-2 分工
  提案 + 附件指针。**用户动作项：转发给王晗。**
- **stage400 进度 13/22**（OB-1..4、M-A1..A4、I-1/2/3、P-1、P-2）。
- **下一优先：P-3（§6-7 装配：paper_full_v1 §4-5 + stage371-381 +
  stage403/405 数据刷新 + 新口径表 686/我方）→ P-4（附录 B/C/D +
  GF(257) 工件打包）→ P-5（NT-1 记号 lint + Bergerat 措辞定稿）→
  D-4（内审两轮）。并行可选：I-5、I-6。**

## 6w. 王晗协作全权化 + D-3 合规（2026-09-09，用户授权轮）

**用户指令**：王晗协作事项由 PI agent 全权负责；需决策处给投稿最优
建议或直接问用户。落地两件：

1. **d1_wanghan_package.md 升级为决策备忘录 v2**：原 8 问全部转为
   **8 项定案**（每项含依据与投稿影响）：D1-1 行 9 替换（正确性
   问题，无可选项）、D1-2 Ψ（不可能性定理支撑）、D1-3 Lemma 1.7
   主引理 + N-S 推论对表、D1-4 正文终倍增/附录 RNS、D1-5 渐近措辞
   （被自家定理 forced）、D1-6 逐 lane 语义 + αβ∈A、D1-7 视为排版
   笔误、D1-8 安全入正文。**论文按定案推进不等候确认**（风险对策
   预置：贡献边界 stage397 + 透明差异表）；王晗需求降级为非阻塞
   确认轮（8 定案过目 + §2/Lemma 1.7 文本整合——两轮未返回则本方
   按 V2 原文整理并入，署名归属不变）。
2. **d3_anonymity_compliance.md（D-3 完成）**：正文匿名 6 项
   （1711 第三人称双版本拆分/草稿差异表不入正文/致谢/工件路径
   脱敏/内部文档排除/无单位）+ ePrint 策略（建议投稿当日贴非匿名
   版确立优先权，两版正文一致 diff 冻结）+ cover letter 要点。

**保留给用户的决策仅两项**（见 d1 §四 / d3 §二.4）：
(a) 转发渠道（d1 备忘录 + v2 骨架发王晗——物理依赖）；
(b) 署名序（建议 A 王晗一作【若完成 §2 整合轮】/ 建议B 用户一作
【若仅确认】）+ ePrint 时序确认（默认当日）。
**stage400 进度 15/22**（+D-1 决策化、D-3）。

## 6x. 协作依赖清零（2026-09-09 用户三项决策）

1. **署名**：挂起至打包前（用户：重点是质量与融合后满足欧密的
   贡献；王晗无署名要求）。
2. **ePrint**：投稿当日贴非匿名版（用户采纳）。
3. **王晗无任何后续材料**（用户明确）→ **全部欠缺内容本方独立
   完成**：§2/Lemma 1.7/Cor 1.8 按 V2 草稿原文整理并入
   paper_full_v2（署名归属透明保留）；确认轮取消。**协作等待项
   清零，投稿时间线无外部依赖。**

D-1/D-2/D-3 全部 CLOSED。

## 6y. WS-C 装配全部完成（2026-09-09 续，P-3/P-4/P-5）

- **P-3**：§6 安全（v1 基底 + r-input 钥束增量段【Ψ-Min：恰 2 把
  aut-KS】）+ §7 实验（**686/我方口径主表**、r-input 新行 7.4、
  **N1 验证节 7.5**【原语 ≤0.3 bit、逐阶段 worst 0.186 bit、镜像
  逐位一致 12/12】、负结果目录更新）+ §8 相关工作/结论。
- **P-4**：附录 A（证明索引）/B（GF(257) 方法论 + 工件表）/C
  （负结果 C-1..C-11 目录）/D（参数表 + 记号-代码映射 + D-3 打包
  规则）。
- **P-5（stage410_p5_notation_lint.md）**：NT-1 六项检查通过
  （记号单一来源/686 口径/代码名仅附录/无草稿引用）；Bergerat
  措辞按 stage388 补审定稿应用（"共享掩码批处理非首创，本工作 =
  稀疏小钥匙域完整实例化"）；引用键清单；两版冻结机制。
- **stage400 进度 20/22**（WS-A 8 + I-1/2/3 + I-4 部分 + P-1..5
  + D-1/2/3）。
- **剩余：D-4（内审两轮：数学审稿人 10 项攻击清单重放 + 实验统计
  口径）→ 端到端打包（BibTeX/sed 脱敏/两版 diff 实操）。可选：
  I-5（r₁⊗r₂ 玩具门）、I-6（FINAL profiler + σ_kg 重标定）。**
  paper_full_v2 已为全结构投稿草（正文 §1-8 + 附录 A-D 就位，
  §3-5 按单一来源指针嵌入，打包时展开为连续正文）。

## 6z. D-4 内审两轮 + I-6 启动（2026-09-09 续）

- **D-4（stage411_internal_review.md）双轮 PASS**：数学轮 10 原项
  全 HOLD + 新素材 8 项 7 HOLD + 1 行动项（N-5：FINAL 参数噪声外推
  → I-6）；实验轮 10/10（修正 v2 §7.1 试次数口径 3→6）。三表即
  回应信预置弹药。
- **I-6 已启动（后台）**：probe_rinput_prof 加 σ 旋钮
  （SAB_RINPUT_SIGMA=-49）与粗测模式（SAB_RINPUT_COARSE=1：仅测
  suba/终态，301 bit 级只算不测，压到 ~1-2h/试）；dell 后台跑
  n=2048/h=42/rp=7/σ_G=2^-49/1 试 → repro_stage405/final_h42.log，
  完成标志 DONE_FINAL。**下一会话收割**：σ_kg 重标定值 + FINAL
  的 N1 终态闭合（预期 even 类 ~2^55-56 ≪ 守卫 2^62；若闭合则
  N-5 攻击关闭、论文 §4/§7.5 补 FINAL 行）。
- stage400 进度 21/22（+D-4）。剩余：I-6 收割（在途）+ 端到端打包
  （BibTeX/sed/两版 diff 实操）+ 可选 I-5。

## 6aa. I-6 闭合（2026-09-09 深夜）

FINAL 参数（n=2048/h=42/ρ=7/σ_G=2^−49）噪声闭合：门 0/4096；DC-游走
49.15 vs 推导 49.20；**终态 meas 2^54.57 = pred 2^54.57（−0.00 bit）**；
pair +0.03；stage 0.020；镜像逐位一致。σ_kg 经验地板不随 σ_G 变化
（原语闭式携带）。**审稿攻击 N-5 关闭**；论文 §7.4/§7.5 已补 FINAL
行。途中修复并入册：RS_sparse_binary_key 第 6 参 = target_r_prec
（非间隙界），target=6 在 FINAL 规模耗尽 2^15 重试返回野指针（gdb
定位）；probe 改 target=7 + 空指针守卫。
**stage400：22/22 全部闭合（除端到端打包实操 + 可选 I-5）。**
下一会话唯一剩余：端到端打包（BibTeX 生成 / sed 脱敏执行 / 匿名
版-ePrint 两版 diff 冻结验证 / ePrint 当日张贴准备）。

## 6ab. 主张-证据全覆盖审计 + I-5 闭合（2026-09-09 终局）

用户指令（一切理论主张/算法须有实验数据支撑）执行完毕：
- **stage412_claim_evidence_audit.md**：正文全部主张 → 证据逐条映射
  （§3/§4/§5/§6-7 四表）+ 6 个非实现项诚实边界（HYB 见证/F3 界/RNS
  替代/HT-10 C 级/σ_kg 地板/奇尾开放——均为非性能主张）。
- **I-5 闭合（scripts/check_ht10_gf257.py）**：HT-10 联合组合
  （r1=2×r2=2）GF(257) 判定 **5120/5120 全等**（vs 4 独立标量
  oracle），负对照触发；实现 = 已验证检查器的薄扩展（导入原语，
  消除转写歧义——首版裸转写因嵌入约定混淆失败，入册教训）。
  HT-10 由"理论-only"升为机器验证；体级密文独立由 M1 C 级门分层
  覆盖（分层注记入 stage412）。
- **至此：正文每一个定理/引理/算法主张都有实验或机器证据。**
  唯一剩余工作 = 端到端打包实操（BibTeX/sed 脱敏/两版 diff）。

## 6ac. 完整手稿交付（2026-09-09，用户指令：V2 风格自含手稿）

- **manuscript_20260909.md**（docs/paper_ccf_a/）：自含核心手稿——
  Abstract / §1 四贡献 / §2 预备（含 [1711] Lemma 1.7 引用域）/
  §3 算法（Alg 1'/2' 伪代码 + 引理 1-6 + 定理 7-9 全证明：H 子群、
  迹提取、U_a 恒等式、奇偶障碍、Ψ、伪差抵消与终倍增、S1 语义、
  C1' 逐步归纳、Ψ-Nec、HT-10 组合）/ §4 噪声（引理 10-12 + 定理 13
  N1 + 推论 14 尺度化统一，全部证明 + 三参数点实测闭合表）/
  §5 复杂度（引理 15-19 + 定理 20-22：三层下界、元数-预算、相位
  独立、LB-F 前沿、摊销定律，证明）/ §6-7 凝结表 / §8 结论 +
  诚实开放项 / 参考键 + 工件指针。
- 闭环判定（答复用户）：**是**——每个定理四件套（显式假设/完整
  证明/机器佐证/实测数据）齐备；三个开放项（DAG 强形式、类普适、
  奇尾逐列代数）文内如实标注且不支撑任何主张。手稿即审稿版核心；
  剩余为排版级工作（LaTeX 化/BibTeX/图表），非内容性。

## 6ad. 全算法盘点 + stage378 闭合（2026-09-10）

- **stage413_algorithm_inventory_audit.md**：9 算法清单（5 实现 + 2
  否定性组 + 2 非实现界）+ 逐算法四层完备性表（理论/正确性/噪声/
  实验）+ 参数集与对照完备性总判。
- **stage378（唯一实质缺口）已闭合**：G-ρ FINAL 门 0/4096×2 配置
  PASS；全钥束实测 keygen 0.7-0.8s ≈ **1.1× 标量族**（论文可写实测
  值）；FINAL 盲旋转 25.9-26.6s。SAB_GRHO_TARGET=7 绕开 RS 陷阱。
- **r-input FINAL 6 试 coarse 升级在途**（DONE_FINAL6；收割后并入
  RESULTS §I-6 行）。
- **下一会话**：收割 6 试 → 端到端打包（BibTeX/sed/两版 diff/ePrint
  准备）。可选项不变（SQ q15、HYB 小参数点缀）。
