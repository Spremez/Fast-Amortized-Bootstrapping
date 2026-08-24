# GOAL: CCF-A 类安全会议论文 —— 自主执行状态

角色: 本 Agent 作为论文唯一作者，负责算法设计、实验、撰写全流程。
目标 venue: CCS / USENIX Security（CCF-A；USENIX Sec'27 周期为主目标，CCS'27 为备选）。
更新: 2026-08-20（自主模式启动）

## 里程碑（关键路径）

| # | 里程碑 | 状态 | 依赖 |
|---|---|---|---|
| M1 | D1 新颖性门 | ✅ PASS（0d444d6） | 9 源哈希绑定 |
| M2 | D2 算子闭合门 | ✅ PASS + 权威重放（b3cf1e9），γ=2 | — |
| M3 | **D3 噪声/安全/成本门** | ✅ **PASS + 权威重放（账本 2c6236c，controller efc47d9）**；悲观投影 1.4599× ≥ 1.10 | stage322/331 实测数据 |
| M3+ | **D0-D3 全准入** | ✅ **`ADMIT_CANDIDATE_D_TO_ISOLATED_ENCRYPTED_OPERATOR_IMPLEMENTATION`，production_hot_path_permission=yes** | M1-M3 |
| M4 | D4-D6 隔离实现→集成→优化 | 🔨 下一主任务（D4：SAB_Operator_State/Key 独立类型，r=1/2/4 相位等价 + microbench，服务器跑） | M3+ |
| M5 | 全矩阵实验（stage355, 11 行） | 🔄 服务器运行中 | — |
| M6 | B2 BatchBoot 复现（head-to-head） | ⏳ | 服务器空闲窗口 |
| M7 | 论文全文 | ⏳ 骨架先行 | D3 结论已定：主贡献 = late-binding 算子 SAB + 强制重随机化发现 + 闭合定理 |
| M8 | 工件打包 + 投稿 | ⏳ | M4-M7 |

### D3 关键科学结论（论文素材）

1. **强制重随机化定理（新发现）**：late binding 把噪声放大 β=√2·‖ΔF‖₂（最坏任意
   LUT、N=2048、2-bit 时 β=32），高斯尾指数除以 β² → 直接绑定把标量 2⁻¹²⁰ 退化到
   2⁻⁰·¹²。构造因此**必须**携带 post-binding 重随机化 KS（σ_flood=2⁻⁸），
   恢复 2⁻¹⁸⁴ ≤ 2⁻¹²⁰ ≤ 2⁻⁶⁴。这是设计文档预留 `d4_rerandomization_if_required`
   钩子的实证激活——论文的核心理论贡献之一。
2. **Amdahl**：选择子环乘 25H→8lH（r 无关），中央 1.86×/悲观 1.46× over B1（>10% 门）。
3. **资源**：D key ≈ B0a 标量钥匙 + 重随机化 KS ≈ 18.7MB ≤ 2×B1（19.2MB）；内存 2g=4
   组件 vs B1 的 (1+r)=5 体。
4. 治理修复：D3 契约遗漏 finite_linear 注册（传递导入必选）→ 新 controller commit
   efc47d9（沿链前进，符合契约的 controller-pinning 模型）。

## 资源分工策略

- **本地（Windows/WSL, 16 核 12GB）**: 理论（检查器/证明文档）、D1-D3 治理流程、
  LaTeX 撰写、小规模验证。WSL 仅做构建冒烟。
- **服务器（autovoice-delld, 104 核 251GB, 6230R）**: 全部正式基准（stage355+）、
  D4-D6 kernel 基准、B2 复现。规范目录 `/home/spz/Fast-Amortized-Bootstrapping-stage355-e1-server/`。
- **并行原则**: 服务器跑数期间本地推进理论/写作，互不阻塞。

## 决策规则（自主执行时遵循）

1. **治理优先**: 仓库的 admission 流程（D0-D8）是论文可信度的骨架，不绕过；
   production hot-path 权限在 D3 PASS 前保持 false。
2. **诚实口径**: 论文声明必须落在已验证证据内（claim matrix 红线沿用）；
   投影数字明确标注为投影。
3. **止损**: D3 REJECT → F1（MAT-EMPmul 系统论文）为主轴；D3+M5 均不利 →
   TCHES 降级路线（roadmap §5 go/no-go）。
4. **服务器礼仪**: 单次任务化、断点续跑、不占满 104 核（构建 -j32）、磁盘 97% 满不加压。

## 当前会话执行队列

1. ✅ D3 实现 + 全准入（见上表 M3+）
2. ✅ 批判性接收评审（docs/d4_implementation_plan.md §0）：判定"理论已足、
   实测为零"，接收策略定为 Pareto（时间≈BatchBoot 级 + 密钥 3.3–11.5× 小
   + r-LUT 语义 + 机器验证证明），硬判据 A-E 落档
3. ✅ D4 实现契约：include/sab_operator.h（数据结构 + 7 个更新律 API）
4. 🔨 D4 C 实现（src/sab_operator.c + 等价测试 + microbench）——下一主任务
5. stage355 服务器监控（行1 第5样本）
6. B2 复现 + 应用原型（D4 等价测试通过后上服务器并行）

## 运行状态速查（2026-08-23）

- 本机: D4 参考实现已提交主树（`53e7ca9`，编译零警告）；下一项 = 等价测试模式
- 服务器: **2026-08-23 全天不可达**（ping 100% 丢包，疑似关机/离网；需操作者开机）。
  stage355 断点续跑就绪，恢复后自动从缺行继续；数据在盘上安全（最后一次确认：
  行1 SET_8_9_4096_r4 完成 4/10 样本，05:44Z）
- 已修复: 主树 `.git/config` 残留 `core.worktree`（备份于服务器前 /tmp 与本会话记录）


### v3 最终设计（原语探针后确定，2026-08-24）

独立探针（src/probe_mul.c，已提交 924271f）：`polynomial_mul_torus` 对
"满刻度 × 小数值"返回零（N=1024 复现）或 −(A·B)·2⁻⁵³ 的 ε 残差（N=256）；
`init_fft` 已排除。全库通行的正确模式是 trgsw.c:447 外积：
**`trlwe_decompose` 分解密文侧（小数位）× DFT 域满刻度多项式
（`trlwe_DFT_mul_addto_by_polynomial`）**。
v3 绑定 = U 通道按 accumulator gadget（bg_bit=23，l≈3 层）分解，
逐层与 DFT 域 F/τ(F) 相乘后精确移位累加——与系统全部外积同构，
成本 ≈ 3 EP（D3 late_binding_transforms 预算内）。


### v5/v6 与语义证据链（2026-08-24 深夜，探针 src/probe_v6.c）

- v5（精确截断拆分）与 v6（数位×key-DFT，镜像 trgsw.c:447）均数学正确但输出全零；
- setup 经逐项打印验证完全正确（s/pos/符号/±2^62）；
- 量级扫描（16 组）显示 to_DFT→mul_DFT→inverse 对稀疏尖峰输入给出 **纯整数卷积
  mod 2^64** 语义（7/8 行精确符合 (A*B) mod 2^64，非 torus 实数积 (A*B)>>64）——
  这解释 v2-v6 全部症状：2^62 通道系数与 F 的整数积 mod 2^64 仅保留 F 的低 2 位；
- **剩余唯一工作**：精读 execute_reverse_torus64 / polynomial_mul_DFT 的 split-hi/lo
  重组契约（双块布局：Re∈[0,N/2)、Im∈[N/2,N)），按其真实语义重写绑定缩放算术。
  这是收敛后的单点任务，证据链已完整。

### v4 进展（2026-08-24 晚）

v3（数位分解 + torus 域逐层移位）失败：中间层实数值 >1 不可表示（数位×F 的
torus 表示 wrap）——EP 的真实做法是 DFT 域累加、单次逆变换。v4 据此重写：
F 的带符号位层（每层 ≤½ 合法 torus）× U 的 DFT（预计算一次），DFT 域点乘累加，
单次逆变换，尾端 <<2 吸收 ¼ 通道缩放。**最终失配 94%（v3）→ 0.1%（2113/2.1M）**。
剩余：stage1 稳定 2048（半数 slot 特征）+ 单元探针零——一个有界 bug，疑似
位层权重/边界符号层的具体定义（层权 2^d 与移位提取位不匹配的候选已记录在
src/sab_operator.c v4 注释与本次会话）。下一步：修正层权定义为
bit(64-prec+d)·2^{64-prec+d} 的 torus 缩放并处理 d=prec 边界，重跑等价测试至 Pass。

## D4 进度

- [x] include/sab_operator.h（契约）+ src/sab_operator.c（参考实现，零警告编译）
- [x] main.c `SAB_OPERATOR_EQUIV_TEST` 运行（构建/执行/插桩全通）——**测试装置本身验证有效**
- [ ] 通道编码 v2：等价测试暴露两个 GF(257) 检查器结构性看不到的真实编码问题：
  1. **单项式不可表示**：torus 上裸整数 1 = 2⁻⁶⁴，算子通道不能携带 X^s 原尺度过
     Δ_op=½ 缩放 + 绑定乘 2F（2F∈(−1,1) 恒可表示，乘积精确）——已实现；
  2. **FFT 精度**：polynomial_mul_torus 为双精度 FFT 基，满刻度 2⁶³ 通道系数使
     绑定舍入误差 ~2⁻²⁰ torus（实测 50% 粗粒度不匹配，与理论吻合）。需要 gadget
     式分解绑定（F 数位分解 + 精确 xai 移位 + 小系数 FFT）或指数域绑定——v2 设计
     待做，属 D3 binding_domain"Torus-scale 证明"义务的实现侧。
  D2 检查器无法发现这两点（GF(257) 精确算术 + 共模调度），D4 等价测试的价值实证。
  3. **+½≡−½ 与原语逐项 wrap**（v2 已实施 + v3 方案确定）：½ 缩放无法编码负环符号
     （2⁶³≡−2⁶³）；¼ 缩放 + F 数位分解后，单元探针（U_id=¼X⁰）证明 bind 仍全零——
     `polynomial_mul_torus` 对 2⁶²×数位 的乘积逐项 mod-2⁶⁴ wrap（2⁶⁶≡0）。
     **v3**：U 系数拆 32 位高/低半（各 ≤2³⁸，FFT 安全），int128 精确重组
     （(chunk·U_hi)·2³² + chunk·U_lo，末次 mod 2⁶⁴ 即 torus 语义），再统一。**v3 最终版另见下一条（原语规范用法）。**
     2^(shift+2) 移位。阶段数据：stage1 失配从 1,045,011（满刻度 FFT）→ 2048
     （wrap 归零定位）→ 待 v3。
- [ ] microbench + D5 集成（服务器恢复后；服务器 8-23 起不可达待开机）
