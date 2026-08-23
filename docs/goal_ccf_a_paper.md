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

## 运行状态速查（2026-08-20）

- 本机: 空闲（无计算任务）
- 服务器: stage355 矩阵运行中（nohup + 断点续跑），进度
  `ssh autovoice-delld "tail -5 /home/spz/Fast-Amortized-Bootstrapping-stage355-e1-server/repro/stage355_server_e1_matrix/raw/driver.log"`
