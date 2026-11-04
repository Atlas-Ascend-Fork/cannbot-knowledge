---
type: Runbook
title: 向量指令按行发散改为行块化，仅限等长逐元素链
description: 每行 5 条向量指令、64 行下来一段因子构建要 320 次调用；把 64 行合成 2×32 行块可降到 10 次，但只在“所有操作数等长、无标量参照”的纯逐元素链上安全。
tags: [task.optimization, topic.programming_model.execution_unit.vector, topic.performance.analysis]
status: stable
sources:
  - resource: https://gitcode.com/cann/asc-devkit/blob/8746f7ced6cef47e3fd7abd64c0eb827e28e2b56/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/SIMD_compute/continuous_compute.md
    role: constraint
  - resource: https://gitcode.com/cann/asc-devkit/blob/8746f7ced6cef47e3fd7abd64c0eb827e28e2b56/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/basic_arithmetic/Muls.md
    role: supporting
created_at: "2026-10-28T10:00:08Z"
updated_at: "2026-10-28T10:00:08Z"
platforms: ["310p"]
---

# 向量指令按行发散改为行块化，仅限等长逐元素链

## 现象

在 310P（dav-m200）上，分块门控前向 kernel 的架构重写把主 kernel 单次耗时降到原版 0.465x 之后，单例 profile 显示 **vec pipe 仍占主 kernel 单次耗时约一半**，是剩下的最大项。数一遍每 chunk 的向量调用次数：

```
qg           320 次/launch
qgB / kqB   1024
kgqB        1280
kq / kg      640
mask        192
dS          268
```

光是 `qgB`+`kqB` 就 1024 次。写法是“每行一次”：

```cpp
            for (int32_t i = 0; i < T64; ++i) {          // qg = q·2^gk
                Cast<float, half>(rV, qk[i * K128], RoundMode::CAST_NONE, K128);
                Muls(eV, gk[i * K128], LN2, K128);
                Exp(e2V, eV, K128);
                Mul(rV, rV, e2V, K128);
                Cast<half, float>(staging[i * K128], rV, RoundMode::CAST_NONE,
                                  K128);
            }
```

64 行 × 5 条指令 = 320 次调用，而这条链是**纯逐元素**的：`q` 转 f32、`gk×ln2`、`exp`、相乘、转回 f16，每个操作数都是 `[64,128]` 里等长的连续行。也就是说这 320 次调用里，绝大多数成本是**每条指令的固定开销**（发射、地址计算），不是计算。

## 适用场景

- 工程形态：Kernel 直调（AscendC 向量指令级优化）。
- API 路径：`Cast` / `Muls` / `Mul` / `Exp` / `Sub` / `Maxs` / `Mins` 的 `calCount` 参数；UB 内连续行块。
- 验证过的平台与 CANN 版本：Ascend 310P（dav-m200）+ CANN 9.1.0。
- 适用粒度：`platform_wide`（向量指令固定开销占比高是执行模型性质）。
- 路线优先级：`recommended_fastpath`，**但只对“所有操作数等长且无标量参照”的链**。
- 不适用 / 未验证场景：含“每通道一个标量”参照（如带参照 ρ）或含 clamp 的链——本轨迹在该类链上做块化**失败**（见失效边界与反例）；未在 A2/A3 验证固定开销占比（未验证）。

## 根因

向量指令的成本 = 固定开销（发射、地址/掩码准备、pipe 排队）+ 与 `calCount` 近似线性的计算成本。当 `calCount` 只有 128 个元素时，固定开销占绝对主导。

本例每行 128 元素、5 条指令、64 行 → 320 次发射；把 32 行合成一次（`calCount = 32 × 128 = 4096`）后，同样 5 条指令只需 10 次发射。**改动前后计算量一字不差，只是发射次数少了 32 倍。**

关键前提（决定能不能合并）：一次调用只接受**一个 `calCount`**，它同时作用于所有操作数。所以只有当**所有操作数在这段区间上都连续、且长度都 ≥ `calCount`** 时，合并才是等价的。本例 `qg/kq` 链的操作数是 `qk` 的整行块、`gk` 的同一行块、`eV/e2V/rV` 三个满 tile 暂存——全部等长连续，安全。

## 解决配方

`before`（每行一次，`qg` 与 `kq` 各 320 次调用）：

```cpp
            for (int32_t i = 0; i < T64; ++i) {          // qg = q·2^gk
                Cast<float, half>(rV, qk[i * K128], RoundMode::CAST_NONE, K128);
                Muls(eV, gk[i * K128], LN2, K128);
                Exp(e2V, eV, K128);
                Mul(rV, rV, e2V, K128);
                Cast<half, float>(staging[i * K128], rV, RoundMode::CAST_NONE,
                                  K128);
            }
            pushAt(A_QG, staging, T64 * K128 * 2 / 32);
```

`after`（2 个 32 行块，10 次调用）：

```cpp
            for (int32_t h = 0; h < 2; ++h) {          // qg = q·2^gk（32 行块）
                const int32_t rb = h * 32 * K128;
                Cast<float, half>(tD, qk[rb], RoundMode::CAST_NONE, 32 * K128);
                Muls(t2, gk[rb], LN2, 32 * K128);
                Exp(t2, t2, 32 * K128);
                Mul(tD, tD, t2, 32 * K128);
                Cast<half, float>(staging[rb], tD, RoundMode::CAST_NONE,
                                  32 * K128);
            }
            pushAt(A_QG, staging, T64 * K128 * 2 / 32);
```

`kq` 同构替换（`pushAt(B_KQ, ...)`）。注意两个细节：

1. 块化后要换用另一组暂存（`tD/t2` 而不是 `rV/eV/e2V`），因为 32 行块需要的容量是逐行版的 32 倍；这几个 tile 在该相位空闲，属安全的 UB 复用。
2. `pushAt` 仍然推整张 `staging`（`T64 * K128 * 2 / 32` 个 32B 块）——块化只改“算”，不改“推”。

## 设计决策

- 为什么按 32 行而不是 64 行一次？64 行一次需要 `calCount = 8192`，中间的 `Exp` 与两个满 tile 暂存同时占用 UB 会超预算；32 行块在 UB 与发射次数之间取平衡（10 次 vs 5 次，收益差 5 次发射，不值得多占 16KB）。
- 为什么这条链可以块化而“带因子”链不行？判据是**操作数长度是否天然等长**：本链全是整行块；带因子链要先与“每通道一个标量”的 ρ 相减，ρ 只有 128 个元素（见同批精度类卡），块化后 `calCount > ρ 切片长度` 会越读。
- 被放弃的候选：把含 clamp 的 `kqB/qgB` 也块化——试过，引发持续多轮的错坏，最终回退逐行；**性能上确实更想要，但正确性代价不可控**。
- 当前方案属 `recommended_fastpath`。

## 系统信息

- 平台：Ascend 310P（dav-m200），CANN 9.1.0，UB 240KB / 8 核。
- 相关文件：`kernel/<generic>_chunk_kda.cpp`（`qg/kq/kg` 构建段、`staging`/`tD`/`t2` 暂存、`pushAt`）；`host/<generic>_host.cpp`（GM scratch 与 staging 张量）。
- 测量：单例 `msprof ... --task-time=on` 的 `op_summary*.csv` 取主 kernel 的 `vec` 列；主 caliber 用 `--compare --warm-up=3`。

## 性能影响

参照路线：**同一个 kernel 块化前的逐行版本**，来源平台 310p，主 caliber = msprof kernel 级 `Task_Duration`。

- 仅本项（`qg`+`kq` 两段 64 行 → 2×32 行）：主 kernel 单次耗时降到 **0.937x**（约 −6.3%）；
- 同一轮相邻的另一项优化（`kgqB` 显著行截断，另卡）单独降到 0.911x；两项叠加后到 **0.854x**；
- 精度未退化：块化前后同构 emulation 比对与最终全量精度 40/40 均通过（见验证信号）。
- 该路线属 `recommended_fastpath`，无精度取舍（前提是操作数等长）。

## 预防

- 块化前对每条指令列出“操作数 → 物理长度”：**任何一个 < `calCount` 就不能块化**（`LocalTensor` 切片不会报错）。
- 优先块化“纯逐元素、全等长”的链（`qg/kq/kg` 这类）；凡出现“每通道一个标量/每行一个标量”的参照或 clamp 上下界，先按 `calCount` 语义核对，再决定是否块化。
- 块化后用同构 emulation 跑 ring 级误差（目标 ~1e-05），不要只看最终精度门——块化的错坏常常是“部分行偏移”，最终门可能刚好过关。

## 验证信号

来源：分块门控前向 kernel（310P）在架构重写之后的向量调用数削减。以下均为本轨迹内的工具输出。

- 块化前 `vec` pipe 占主 kernel 单次耗时约一半，`qgB+kqB` 一段共 1024 次向量调用（来源平台：310P；证据等级：tool_observed）。
- 本项落地后主 kernel 单次耗时降到块化前的 0.937x（约 −6.3%）（来源平台：310P；证据等级：tool_observed）。
- 块化后（另加 `kgqB` 显著行截断，两项同轮落地）：相对块化前基准，主 kernel 单次耗时先到 0.911x（−8.9%，`vec` pipe 0.882x）、两项叠加到 0.854x（来源平台：310P；证据等级：tool_observed）。
- 精度未退化：该轮之后同构 emulation 的 ring 误差处于 1e-05 量级、全量精度 40/40 通过（来源平台：310P；证据等级：tool_observed）。

## 失效边界

- **含“每通道一个标量”参照的链不能块化**：ρ 是 128 元素切片，块化后 `calCount = 32×128` 会越读相邻 UB，症状是误差随带边界跳变（见同批精度类卡）。
- **含 clamp 的链在本轨迹里块化失败且根因未隔离**：把 `qgB/kqB`（含 `Maxs/Mins` 与 ρ 相减）块化后，即使修掉越界仍出现随 UB 布局漂移的错坏，最终整体回退逐行；教训是“clamp + 标量参照”组合的块化必须逐段 bisect，不能一次上。
- UB 预算：32 行块需要更大的暂存，`calCount` 越大占 UB 越多；240KB 打满时块尺寸要退。
- 未验证场景：A2/A3 上向量指令固定开销占比（未验证，推断可迁移的是“减少发射次数”的思路）。
- 未决项：`qgB/kqB`（clamp + ρ）块化后的残留错坏根因未定位——下个接续点是在容量核算严格的独立缓冲上，只块化“不带 clamp 的 ρ 相减段”、clamp 仍逐行，逐段 bisect。

## 坏实践

- 无脑把“每行一次”改成“每 32 行一次”，不看操作数长度——`LocalTensor` 不报错，错的是数值。
- 用 `rV/eV/e2V`（逐行版的暂存）直接承载 32 行块——容量不足，越界写邻居。
- 只测最终精度门就宣布块化成功；块化的错坏常表现为“特定行/带偏移”，最终门可能仍在门限内。

## 误诊

- 推断（非实测）：起初把 `vec` 高归因于 `Exp`（超越函数慢）；块化后 `Exp` 调用次数同步降 32 倍而耗时只降约 6%，据此认为主项是发射次数而不是 `Exp` 本身——未做“同发射次数换 `calCount`”的对照。
- 推断（非实测）：“成本主要是发射固定开销”依据是“计算量不变、发射次数减 32 倍、耗时随之下降”，未做受控 A/B。
- 推断（非实测）：两项优化各自的 0.911x / 0.937x 归因来自相邻两次单例 profile 的差值，**不是独立 A/B**（两次构建之间只改了对应一段）。
- 推断（非实测）：曾以为块化收益会随 `calCount` 线性增长；32 行 → 64 行的边际收益很小，且 UB 代价翻倍。
