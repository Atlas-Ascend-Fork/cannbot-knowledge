---
type: Optimization
title: "X190: 依赖轴对齐分核的无屏障阶段融合"
description: "多阶段向量链路能合多少阶段取决于依赖图的形状，而不是阶段数量；按依赖轴对齐分核可消掉跨阶段 barrier，实现无屏障融合。"
tags:
  - task.optimization
  - topic.compute.neighborhood.convolution
  - topic.attention
  - topic.programming_model.execution_unit.vector
  - topic.data_movement.data_copy
  - topic.memory
status: stable
sources:
  - resource: https://gitcode.com/cann/asc-devkit/blob/639b2b5c1031188107d23d785d52b935f1b4f13b/docs/zh/guide/operator_practice/simd_operator_optimization/pipeline_scheduling/enable_iterate_avoid_sync.md
    role: primary
  - resource: https://gitcode.com/cann/asc-devkit/blob/639b2b5c1031188107d23d785d52b935f1b4f13b/docs/zh/guide/operator_practice/simd_operator_optimization/pipeline_scheduling/pipeline_scheduling.md
    role: supporting
  - resource: https://gitcode.com/liuyu15819/cannbot-skills/blob/f549d6d3320ac49e3e6e766600fd32bbaf37782a/cases/disc_x190.json
    role: evidence
created_at: "2026-10-29T00:00:00Z"
updated_at: "2026-10-29T00:00:00Z"
platforms:
  - a2
---

> 迁移自 cannbot-skills `plugins-community/ops-perf-evolution/skills/evolution-knowledge/references/okf/`（原 OKF v1 卡，编号 X190）。
>
> 原始元数据：
>
> ```yaml
> id: X190
> origin: discovered
> confidence: single_op
> op_families: [cv-mix, matmul, elementwise]
> bottlenecks: [no_overlap, tiling_imbalance]
> ```

> 证据：基线/变体与逐 case 数据见 [证据包 cases/disc_x190.json](https://gitcode.com/liuyu15819/cannbot-skills/blob/f549d6d3320ac49e3e6e766600fd32bbaf37782a/cases/disc_x190.json)。
> 平台说明：`a2` 对应 Ascend 910B 系列（本卡实测型号见正文）；`a3` 对应 Ascend 910C 系列。

# X190: 依赖轴对齐分核的无屏障阶段融合

## 核心思路

一条多阶段向量链路（本例 8 个 launch）里，能合多少阶段**不取决于阶段数量，取决于依赖图的形状**。
做法是先数出真正的跨阶段依赖，再看哪一条可以被「分核方式」消掉：

本例算子 全链只有 4 处真依赖：① conv 写 acc；② 全 b 归约 per-(j,co) 均值；
③ 全 j 归约 S[b,co]；④ 全 co 归约 Z[b,:]=fcW·S。

**关键判据**：只要分核让「一个核拥有一个通道区间 × 全部 j × 全部 b」，那么 ②③ 就退化成
**同一核内的寄存器依赖**，不需要任何跨核同步 —— 于是原本串行的 crop→stats→fin1→smean
可以合成**一个** kernel（fuse1，核内闭合）。④ 的 Z 只有 d≤64 个输出、d·ci ≤ 16k MAC，
于是把 fin2 整个消掉：每个 out 任务**本地重算** Z（1e2 量级 MAC 换掉一次 10–14us 的 launch ramp），
fin2+out 合成 fuse2。

结果：`prep → conv → fuse1 → fuse2`，**8 → 4 launch**，这就是该依赖图的地板。

## 判据与约束

- **先判可合性，再谈融合**：把「阶段间全局依赖」的全部归约轴列出来；若某归约轴可以被选成分核轴
 （一核独占该轴区间，并拥有该区间内全部其它维），该依赖可消；否则不可合。
- **跨 block 的合并必须放弃**：本环境 `SyncAll(MIX_AIC_1_2)` 只按 block 释放、GM mailbox 软件
 barrier 会 aicore timeout。凡需要跨 block 同步才能闭合的融合（本例 prep/conv 与 crop 之间、
 以及把 out 再塞进 fuse1）都不可行，已放弃。
- **★合并后仍只用一套 TPipe**（每个 fused kernel 单 launch、单 TPipe）：融合不是并行多流水，
 而是把多个阶段塞进同一份 UB 生命周期内顺序执行。
- **★未按所有权分核的折叠会精度全错**：若折叠时归约轴没有被某核独占，全 b / 全 j 归约会读到
 别的核尚未写完的部分和。该反例来自本卡前身索引条目的记录，本轮未单独构造反例实测，
 但所有权约束是实现前提（见下「关键坑」）。
- 读改写次序：同一份数据上「写 accC + 累加 sum/sumsq」可同趟完成；但 pass2 求 S 必须**再读 acc**
 而不是刚写的 accC，以避免核内 read-after-write。
- 本地重算的性价比判据：被消掉的那次 launch 的 ramp（本例 10–14us）≫ 重算的 MAC（1e2~1e4）。
 重算次数随分块数放大，需一并计入代价（本例 fuse2 每 (b,通道块) 重算一次 Z）。

## 关键坑（照抄会踩）

2D pad 拷贝在 UB 侧的行距会被 32B 上取整成 `align8(w)`；`w%8!=0` 时每行尾部有空档。
修法：`DataCopyPadExtParams.rightPadding = align8(w)-w` 把空档**补零**，使一个通道块在 UB 里
成为连续 run，归约/仿射可平铺执行；pass2 的 S 再用 `sum_flat − gapLanes·Σ_j relu(bnB_j)`
修正补零 lane 的贡献（等价于旧 smean 的 tail 修正）。另外 Z 的 d 个点积要用 `MulAddDst` 在
`[d][64]` 累加器上并行，末尾 **一次** V_S 同步；逐 lane `Reduce64` 版本是 32 次同步，ci=512 时白花 +22us。

## 量化（本例算子, 910B2C）

- 阶段时长（case 0-27 均值）：`sk_fuse1` **41.4us** vs 旧 crop+stats+fin1+smean **62.3us**；
 `sk_fuse2` **30.8us** vs 旧 fin2+out **31.8us**；`sk_prep` 17.9 vs 20.6；`sk_conv` 154.4 未动。
 （`aic_mte2 0.878` / `aic_mac 0.345`）；继续提升要靠 conv 数据流，不是再合阶段。
- 精度：全 50 case `max|diff| ≤ 1.2e-5`（相对 ≤ 3.5e-6），无 NaN；官方 `evaluate_ascendc.sh`

## 代价与适用边界

- `fuse1` 的并行度 = `ci`（不是 `js·batch·ci`）：ci=32 时 48 个 AIV 只用 32 个 —— 用并行度换掉 3 次 ramp，
 在小 ci 形状上是净赚，但它是该阶段的上限来源。
- `fuse2` 每（b, 通道块）重算一次 Z：ci=512 且 batch=4 时一块图有 16 个块 → 16 次冗余重算，

## 来源

来自内部进化运行；运行标识、设备、用例与逐 case 数据见证据包。

## 验证状态

本卡为 `status: stable`：定量结果与运行标识见证据包 `cases/disc_x190.json`；引用时请结合上文适用条件与失效边界判断适用范围。

