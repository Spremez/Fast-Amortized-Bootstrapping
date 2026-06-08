# 阶段 0: baseline 与性能平台记录

日期: 2026-06-08

## 已确认路线

- 性能平台: WSL2/Linux。Windows + FFNT portable build 只用于构建/正确性 smoke test，不能作为性能结论。
- 优化目标: 吞吐量优先，而不是单个完全独立 bootstrap 的延迟优先。
- `r` 的阶段性定义: 多 LUT / 多 SAB lane，共享同一套 blind-rotation 控制流与 selector schedule。
- 集成方式: 新增 `sab_pvw_*` 路径，不破坏当前 `sab_rlwe_bootstrap` 标量路径。
- 代码策略: 先基于本项目 MOSFHET/SAB 结构补齐 matrix/PVW 外积 kernel；只有在证明不会损失性能时才直接沿用外部项目实现。

## Git baseline

- `b59a125 Initial project version`: 初始导入版本。
- `4537798 Fix portable baseline build`: 当前 baseline 构建修复。

`4537798` 的主要含义:

- 顶层 `Makefile` 保证 `setup` 先于 `main` 构建。
- 补齐 `pvwtmlwe.o` 与 `ffnt.o` 的显式规则。
- `FFT_LIB=ffnt` 映射到 portable build。
- `ENABLE_PVW_TMLWE ?= false`，避免半成品 PVW TMLWE 路径默认进入 baseline。
- Windows portable allocator 保持 `free()` 释放约定。
- `.gitignore` 忽略生成的 `main.exe`。

## Windows portable smoke test

命令:

```powershell
make -B FFT_LIB=ffnt A_PRNG=none ENABLE_VAES=false PARAM=SET_2_3_2048 ARCH_FLAGS="-march=haswell"
```

结果: 构建通过。

限制:

- 该路径使用 FFNT portable FFT，仅用于 Windows 可构建性与后续小参数正确性 smoke test。
- Windows FFNT 完整 `main` 在 60 秒内未完成，已终止；不能用该结果判断 686 SAB 性能。
- 当前源码存在若干 Windows `printf` format warning，尚不影响 baseline 构建。

## WSL/Linux 性能平台

环境快照:

- WSL: Ubuntu, WSL2 kernel `5.15.167.4-microsoft-standard-WSL2`
- CPU: Intel Core i7-11700, 16 vCPU exposed to WSL
- Toolchain: GCC 13.3.0, GNU Make 4.3
- CPU flags include AVX2/AVX512/VAES-class capabilities;后续性能结论需固定具体 `FFT_LIB`、`ENABLE_VAES`、`ARCH_FLAGS` 与 CPU governor/context。

构建命令:

```bash
make -B FFT_LIB=spqlios A_PRNG=none ENABLE_VAES=false PARAM=SET_2_3_2048
```

结果: 构建通过。

完整 baseline run:

```bash
timeout 180s ./main
```

输出摘要:

```text
Sparse bootstrapping with binary keys
Input: N=2048, h=39, binary, sigma=2^-15
Packing: N=2048, h=256, ternary, sigma=2^-44
Output: N=2048, h=512, ternary, sigma=2^-50
Decomposition: BS(l=1, beta=2^23) PCK(l=2, beta=2^14) KS(l=12, beta=2^1)
Message precision: 3 - Repetitions: 3
Max monomial distance logB: 7
Rejection Sampling Attempts: 90
Bootstrapping time: 16,582,619 us +- 72,520.581010
Pass
```

记录解释:

- 当前默认验证参数为 binary `SET_2_3_2048`。
- 实际 `r_prec` 由 `get_min_prec(input_key)` 在 rejection sampling 后得到；本次 run 为 7，与 `target_r_prec=7` 一致。
- WSL stderr 出现过宿主网络/localhost 相关噪声，不属于程序失败。

## 后续阶段 0 核验口径

- 每次性能比较都必须记录: commit hash、平台、`FFT_LIB`、`A_PRNG`、`ENABLE_VAES`、`PARAM`、`KEY`、`ARCH_FLAGS`、重复次数、是否开启 instrumentation。
- Windows/FFNT 只回答“是否能编译/小样例是否仍正确”。
- Linux/spqlios 或明确 AVX 路径才回答“是否更快”。
