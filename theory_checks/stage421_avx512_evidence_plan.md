# stage421：batching/joint 的 AVX-512 优化实测 + 完备正确性证据链 + 总体流程规划

Date: 2026-09-10（晚，stage420 之后）。用户指令（本轮纲领）：
packing 已达 ~1.8× 实测（用户归因 AVX-512 优化栈），batching 与联合
算法必须同栈优化后实测；补理论加速比与渐进复杂度；packing/batching
必须**完备、可证、可验**——用充分测试案例从代码给出正确性数据 +
自举功能性实例数据（辅助证明，非论文内容）；完整规划后续所有流程
并执行。

## 〇、总体规划（工作流分解与状态）

| WS | 内容 | 状态 |
|---|---|---|
| WS-1 | AVX-512 七旗标构建（pathA 栈）+ binary 路径 pack/batch/joint 重测 | ✓ 完成（本机=正确性层；AVX-512 权威口径归 WS-7/dell） |
| WS-2 | include-zero 执行路径（1.8× 同族）接入探针 + 调度无关性强测试 | ✓ 完成（全 PASS） |
| WS-3 | 功能性门（库约定：半域消息 + 负循环 LUT + 期望值对拍 + 余量统计） | ✓ 完成（9 配置模式全 PASS） |
| WS-4 | 理论定稿：三轴加速比公式、渐进复杂度、AVX-512 常数效应、对账表 | ✓ 完成（§五-§六） |
| WS-5 | handoff/文档/提交 | ✓ 完成 |
| WS-6 | KS 版 b′ 真实门（预对齐从明文模拟换真 keyswitch） | ✓ 完成（见 §五b） |
| WS-7 | dell 生产口径三表复跑（含七旗标 AVX-512 层 + FINAL 多配置） | ✓ 完成（§五c；FINAL 三轴 1.60×±1% 命中理论） |
| WS-8 | +257 常数形式化推导（并入正确性定理证明） | 后续会话 |
| WS-9 | 行瓦片 EP 内核对 bodies=8 的扩展（若 dell 后仍有缺口） | 视 WS-7 结果 |
| WS-10 | 论文侧并入（§3 算法/§4 噪声/§5 复杂度/§7 实验四章联动改写） | WS-6/7 后 |

## 一、WS-1 设计：AVX-512 七旗标栈（pathA，与 1.21×/1.81× 同栈）

构建定义（stage371/355 生产口径原样复用）：
```
MAT:   -DMAT_TRGSW_AVX512_SMALLR_SPECIALIZED -DMAT_TRGSW_SUB_DECOMP_DFT_DIRECT -DMAT_TRGSW_AVX512_SUB_DECOMP
PVW:   -DSAB_PVW_BACKEND_FROM_DFT_ADD -DSAB_PVW_SUB_DECOMP_FUSION -DSAB_PVW_DUAL_SUB_CMUX -DSAB_PVW_SUBA_INCLUDE_ZERO_COEFF_ONE_FAST
FFT:   -DUSE_SPQLIOS -DAVX512_OPT（spqlios-fft-avx512 / ifft-avx512 / impl-avx512）
```
CPU 前提：本机 WSL 具备 avx512{f,bw,dq,vl,vbmi,ifma} ✓。
对照层：同源码未旗标构建（stage420 已测）→ 旗标增量可分离。

## 二、WS-2 设计：include-zero 路径 + 调度无关性强测试

- 探针加 `SAB_PA_INCLUDE_ZERO=1`：key 换
  `sab_pvw_new_nonbinary_key(..., include_zeros=true, ternary=false)`、
  管线换 `sab_pvw_sparse_mul_nonbinary`（COEFF_ONE_FAST 快路径生效，
  系数全 1 的密钥下 sub_a 与 binary 同为明文单项式）。
- **调度无关性强测试**：联合侧用 include-zero 调度（含 padding 步），
  oracle 侧保持 binary 调度——两者调度不同、终端指数恒等式（方向 A
  形式，仅依赖密钥支撑）预言仍一致。padding 激活配置：
  n=1024/h=6/rprec=4（平均间隙 ~146 > r_max=16 → 每间隙 ~9 padding 步）。
  通过 = "预对齐与站点调度无关"的直接机器证据（远强于单调度等价）。
- n=256/h=6（无 padding）也跑：验证 nonbinary 代码路径本身。

## 三、WS-3 设计：功能性门（库约定锚定）

- 消息半域：msgs = int2torus((t+3l) & (2^(p−1)−1), p)（值域 [0,2^(p−1)),
  负循环反周期域内，与 main.c 功能测试一致）。
- TV：库 `sab_LUT_packing` 构造逐式复刻——b[0]=v(LUT[0])，
  b[N−i]=−v(LUT[i/(N/2^(p−1)))])，LUT 值随机 ∈ [0,2^(p−1))。
- 期望值：joint 与 oracle 双侧 decoded == LUT_ch[value(m_l[t])]；
  逐槽余量 |phase − v·2^61| 统计（max/rms，对照判决余量 2^60）。
- 环境变量 `SAB_PA_FUNC=1`；跨配置 × reps 运行。
- 证据意义：等价门（joint==oracle）证明"与已验证标量自举一致"；
  功能门证明"自举语义本身正确（LUT 求值可解码）"——两者合起来才
  是完整正确性链。

## 四、WS-4 理论定稿要点（详见 §五-§七）

- 三轴加速比（vs 标量基线）：pack 2r₂/(1+r₂)、batch 2r₁/(1+r₁)、
  joint 2r₁r₂/(1+r₁r₂)；vs 分离 packing：r₁(1+r₂)/(1+r₁r₂)。
- 渐进：Θ((h+1)ρℓN log N·(k+r)/r) 每消息，r→∞ → k/(k+1)·基线 =
  2× 上限（k=1）；AVX-512 不改渐近，只恢复行计数常数（行瓦片 +
  融合消除每行固定开销）。
- 判据：旗标实测实现率应显著回升（未旗标 bodies=8 仅 56-58%）；
  若仍不足 → WS-9 内核扩展。

## 五、执行结果（2026-09-10 晚回填）

### WS-1：AVX-512 七旗标栈实测（本机 WSL）

**旗标二分定位**：MAT 层（SMALLR_SPECIALIZED+SUB_DECOMP 族）单独 ✓；
PVW 层（BACKEND_FROM_DFT_ADD+SUB_DECOMP_FUSION+DUAL_SUB_CMUX+
COEFF_ONE_FAST）单独 ✓；**spqlios avx512 FFT 汇编在本机段错误**
（ifft 尾置链接序也无效；与 §6j MinGW 缺陷同类的本机限制）。
FMA FFT + 完整七旗标 = 稳定，**全部正确性门 PASS**。

**玩具尺度（n=256/h=6，6 reps 中位数，speedup=基线/联合）**：

| 轴 | 配置 | plain | 七旗标 | 理论(vs标量) |
|---|---|---|---|---|
| pack | r2=2 / r2=4 | 1.185 / 1.249 | 1.230 / 1.234 | 1.333 / 1.600 |
| batch | r1=2 / r1=4 | 1.194 / 1.242 | 1.180 / 1.239 | 1.333 / 1.600 |
| joint | 2×2 / 4×2 / 2×4 | 1.227 / 1.033 / 0.994 | 1.245 / 1.025 / 1.004 | 1.600 / 1.778 |

同会话交替 A/B：**玩具尺度旗标无增量**（±噪声内）——行瓦片/融合
优化面向 FINAL 尺度；玩具 bodies=8 的缺口是工作集缓存受限（~37MB
累加组），旗标不解决。

**FINAL（n=2048/h=42，2×2，同会话配对）**：plain **1.204×**
（67.4s/81.1s，门 0/8192）；七旗标 **1.030×**（90.4s/93.1s，门
0/8192）——**本机旗标反而更慢**：客户端 CPU 的 AVX-512 降频特征；
旗标栈为 dell Xeon 调优。**结论：AVX-512 层的权威数字必须在 dell
实测（WS-7）**；本机 WSL 定位为正确性层。构建配方已沉淀
（build_wsl/pa2_avx 同构，dell 直接复用 stage371 的 FLAGS/PATHA）。

### WS-2：include-zero 路径 + 调度无关性

- include-zero 执行路径（sab_pvw_new_nonbinary_key + 
  sparse_mul_nonbinary，COEFF_ONE_FAST 快路径）：plain（2×2、1×4）、
  七旗标（2×2）、include-zero+功能（2×2）**全部 PASS**。
- **调度无关性**（SAB_PA_ORACLE_RPREC 解耦）：joint 六级蝶形 vs
  oracle 七级蝶形（同一钥不同调度）：等价 0/1024 + 功能 0/2048（4×2）
  **双 PASS**——终端语义只依赖密钥支撑（方向 A 闭式的直接推论）
  再次机器确认。rp=5 在 n=256/h=6 结构性不可行（7 间隙×≤31<256）。
- 途中发现并修复：`RS_sparse_binary_key` 重试只查站间间隙、**不查
  最终环绕间隙**——探针侧加了全间隙检查重试环（keygen 健壮性入册）。

### WS-3：功能性门（库约定锚定，全部 PASS）

配置 (1,1)/(1,4)/(2,2)/(4,2)/(2,4) × 含 4-reps、toy h=1、include-zero、
调度无关功能模式——**双侧（oracle 与联合）解码全部等于明文期望
LUT 值**，0 失配。余量统计（判决边界 2^61）：

| 侧 | margin max | margin rms |
|---|---|---|
| oracle | 2^48.3–48.9 | 2^46.9–47.0 |
| joint | 2^54.0–54.4 | 2^52.5–52.9 |

联合侧比 oracle 高 ~6 bit = 预对齐的 h+1 次独立 modswitch 舍入
（与 stage419 指数层结论一致），**距判决边界仍余 ≥6.6 bit**。
功能性实例数据样例（FUNC-DEMO，2×2 试，(l,j,t)|消息|期望|oracle|联合）：

```
(0,0,0)|0|1|1|1   (0,0,1)|1|1|1|1   (0,1,0)|0|0|0|0   (0,1,1)|1|0|0|0
(1,0,0)|3|0|0|0   (1,0,1)|0|3|3|3
```

## 五b、WS-6 执行结果：KS 版真实预对齐（2026-09-10 深夜补）

探针新增 `SAB_PA_REALKS=1`（KS 参数 SAB_PA_KS_T/BB，默认 t=12/bb=1）：
d = (a_c − a_l, 0) 虚拟样本 → `trlwe_keyswitch`（s→s 同钥）→ 取**相位**
得 −d⊗s + KS噪声 → b′ = b_l − 相位。这是真实系统会跑的密码学操作
（每输入一次标准 keyswitch）。

**结果（n=256/h=6）**：
- b′ vs 精确模拟偏差：max 2^55.8 / rms 2^54.4 = 纯 KS 噪声
  （独立原语测试 kstest.c 交叉验证同量级 2^55.7）。
- **等价门 0/1024 PASS；功能门全 PASS**（2×2、4×2×3 reps、
  include-zero 组合）。
- 联合侧功能余量 max 2^54.0 —— 与明文模拟版（2^54.0–54.4）**同级**：
  KS 噪声在预算内不可见（√合成后仍 ≪ 2^61 边界）。
- KS 成本：~32 μs/试验（r1=2 输入），占联合管线 1.3s 的 0.002%
  ——理论"每输入一次 KS = 低阶项"获实测确证（含预对齐的 speedup
  与不含相同，1.184×）。

**实现坑入册**：`trlwe_keyswitch` 输出是**非零 mask** 样本
（out = (−as_a, in->b − as_b)），相位需经 trlwe_phase 提取；直接取
裸 out->b 会引入 ~2^63 的 as_a⊗s 伪差（首版失败根因，诊断链：
参数扫描排除分解尾部 → 双符号判别排除全局符号 → 独立原语测试
隔离库侧 → 定位用法）。

**结论**：E1-E9 证据链升级为**密码学真实版**——预对齐联合管线在
真 KS 噪声下功能等价、余量同阶、成本可忽略。剩余唯一开口 =
dell 性能口径（WS-7）。

## 五c、WS-7 收割：dell 权威数字（2026-09-10 深夜）

**两个前置修复**（否则 avx512 层崩溃）：
1. 库 bug：execute_{reverse,direct}_torus64(_add) 的 AVX512_OPT 路径
   对外部 safe_malloc 缓冲（16B）做对齐向量访问 → 布局依赖段错误；
   已改 loadu/storeu（生产 E1 是布局运气通过）。
2. 构建配方：**AVX512_OPT 必须全局**（misc.c 的 safe_aligned_malloc
   仅在见宏时用 posix_memalign(64)）——此前"avx512 FFT 汇编崩"
   的两例（WSL、dell 首跑）真因均为把宏限定在 FFT 文件。

**结果**（详见 stage420 §四b）：dell flag（spqlios_avx512+七旗标）
全部门 PASS（玩具双层级 + FINAL 0/8192×3 + 0/16384 + func FINAL
双侧 0/8192）；FINAL 三轴 bodies=4 全部 **1.597-1.618× vs 理论
1.600×（±1%）**；旗标增量 +21%（1.618 vs 1.340 同会话配对）；
bodies=8 = 64%（WS-9 目标）。WSL 负增量确认为本机 CPU 特征而非
实现问题。

## 六、理论定稿（三轴统一）

**加速比公式**（vs 每消息一次标量自举基线）：
pack 2r₂/(1+r₂)；batch（预对齐）2r₁/(1+r₁)；joint 2r₁r₂/(1+r₁r₂)。
vs 分离 packing 基线：r₁(1+r₂)/(1+r₁r₂)。

**渐进复杂度**：每消息 T(r) = Θ((h+1)·ρ·ℓ·N log N · (k+r)/r)；
r→∞ → k/(k+1) · 标量 = **2× 上限**（k=1）；预对齐附加 r₁ 次输入环
KS（低阶）。与 stage398/399"匹配下界 + 行常数 (k+1)→1"定案一致；
**AVX-512 只改常数不改渐近**——其行瓦片/融合消除每行固定开销，
收益是机器相关的（本机负、dell 正，见 §五）。

**理论-实测对账判据**：bodies≤4 时实现率 77–93%（plain 玩具）；
bodies=8 玩具 ~57%（缓存受限，需 WS-9 或 FINAL 尺度）；FINAL plain
同会话 1.204/1.600 = 75%（vs 分离 packing 口径 = 1.204×0.75 =
0.90×——dell stage417 直接配对曾测 1.197× vs 理论 1.200×）。
**待 dell（WS-7）后旗标口径对账定稿。**

## 七、正确性证据目录（主张 → 仪器 → 结果）

| # | 主张 | 仪器 | 结果 |
|---|---|---|---|
| E1 | 联合管线 ≡ 逐输入标量自举（等价） | PA2-GATE 全配置矩阵 | 0 失配（含 FINAL 0/8192） |
| E2 | 自举语义正确（LUT 求值可解码） | FUNC-GATE 明文期望对拍 | 双侧 0 失配 ×9 配置模式 |
| E3 | 终端指数闭式（±分裂=负循环绕回） | SAB_PA_TRACE 指数提取 | 双路径全槽精确（+257 常数） |
| E4 | 与站点调度无关 | ORACLE_RPREC 解耦 | rp6-vs-rp7 等价+功能双 PASS |
| E5 | include-zero 执行路径语义不变 | INCLUDE_ZERO 模式 | 0 失配 ×4 模式 |
| E6 | 噪声余量充足（功能性稳健） | FUNC-GATE margin 统计 | joint max 2^54.4 vs 边界 2^61 |
| E7 | 失败根因受控复现 | SAB_PA_LUT_FINE | 107/256 机制复现（刃锋） |
| E8 | 多参数/多 seed 稳定 | h∈{1,3,4,6}, outN∈{2048,4096}, 4 seeds | 全 PASS |
| E9 | 预对齐噪声代价 = h+1 次 modswitch 舍入 | E6 余量差 vs oracle | ~6 bit 实测 ≈ 理论 |

诚实边界：b′ 仍为明文模拟（真实 KS 为 WS-6）；AVX-512 权威口径
待 dell（WS-7）；bodies=8 玩具尺度缓存缺口（WS-9 候选）。

## 八、复现

```bash
# 本机 WSL（正确性层 + plain 相对性能）
cd build_wsl/pa2 && ./probe_prealigned2                      # 等价门+计时
SAB_PA_FUNC=1 ...                                            # 功能门+余量+demo
SAB_PA_INCLUDE_ZERO=1 / SAB_PA_ORACLE_RPREC=7 SAB_PA_RPREC=6 # 路径/调度
SAB_PA_TRACE=1 SAB_PA_LUT_FINE=1                             # 指数提取仪器
# dell（AVX-512 层，WS-7）：stage371 FLAGS/PATHA + 本探针（构建配方同 pa2_avx）
```
