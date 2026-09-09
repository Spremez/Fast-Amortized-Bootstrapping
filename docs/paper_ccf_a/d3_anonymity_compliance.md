# D-3 匿名合规清单与投稿/ePrint 策略（PI 执行记录）

Date: 2026-09-09
义务：stage400 WS-D / D-3（0.25 会话）。范围：Eurocrypt 2027 匿名
投稿合规 + 工件打包策略 + 1711/王晗草稿的归属处理。
执行人：PI agent（用户授权全权）。

---

## 一、正文匿名合规（P-2/P-3 装配时逐条过检）

| # | 项 | 规则 | 落实 |
|---|---|---|---|
| 1 | 1711 自引 | 匿名版以第三人称引用（"[Wang et al., ePrint 2025/1711]"），正文可写 "one instantiation of the inner primitive [1711]"；**作者重叠与"内层子运算为我们前作"的叙事只进 non-anonymous cover letter** | §1 定位段（paper_full_v2）拆两版：匿名版第三人称 + cover letter 版完整披露 ✓ |
| 2 | 王晗草稿差异表 | stage406 §3.7 差异表为**内部协作文件**，论文正文不引用"draft/v2"字样；三修正件以我们的设计决策呈现（"we use / we prove"），原稿框架归属在 cover letter 的贡献声明 | 装配 P-2 时 lint：正文禁 "draft/王晗/V2 草稿" 字样 ✓ |
| 3 | 致谢 | 匿名版删除；致谢信息进 cover letter | P-5 检查项 |
| 4 | 工件路径/主机名 | GF(257) 检查器与 repro 脚本不得含 D:\ 路径、dell 主机名/IP、用户名；打包时统一脱敏（脚本头加匿名声明） | P-4 打包时执行（sed 清单另列） |
| 5 | 代码仓 | 工件 = scripts/*.py + 输出日志 + repro shell（重跑指南），不含本仓 git 历史/内部文档（theory_checks、HANDOFF 全部排除） | P-4 |
| 6 | 资助/单位 | 匿名版无；cover letter 声明 | P-5 |

## 二、ePrint 与投稿策略（建议，含用户确认点）

1. **时序**：Eurocrypt 2027 投稿（匿名）当日/次日在 ePrint 张贴
   **非匿名版**（含 1711 作者重叠披露与完整致谢）。理由：
   (a) 确立优先权（下界定理与 DC-游走为强主张）；
   (b) Eurocrypt 允许 ePrint 并行张贴；
   (c) BatchBoot 重评等敏感比较在 ePrint 版保持一致口径。
2. **两版差异冻结**：匿名版与 ePrint 版仅差 作者块/致谢/cover
   letter 内容；P-5 lint 时生成 diff 证明正文一致。
3. **备选会**：CRYPTO'27（若 Eurocrypt 滞后）；TopConf 后备线
   已在 roadmap（不改投稿主张）。
4. **用户确认点**：ePrint 张贴时序（当日 vs 录用后）——默认建议
   当日；如王晗方面有异议可推迟到其确认轮结束。

## 三、cover letter 要点（投稿时生成）

- 1711 关系与作者重叠完整披露（内层原语归属 + 本工作外层贡献）
- 王晗协作贡献声明（§2/Lemma 1.7/Alg 1-2 原稿框架）+ 我方修正件
  清单（F-i/ii/iii）——对应 d1 决策备忘录
- BatchBoot 重评工件声明（公开参数 + 标准 lattice-estimator，全部
  repro 可溯源）
- 工件打包说明（GF(257) 检查器 = 语义级 oracle 等价的方法学定位）

## 四、状态

- [x] 合规清单成文（6 项正文 + 4 项策略）
- [x] 1711 双版本拆分方案（匿名第三人称 / cover letter 完整披露）
- [ ] P-4 打包时执行脱敏 sed 清单（届时生成）
- [ ] 用户确认：ePrint 时序（默认当日，见 §二.4）
