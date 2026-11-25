---
type: Optimization
title: "X122: L0C 满额单累加器时把 cube 调度 CFG_NORM 换成 CFG_MDL"
description: "L0C 被单个累加器占满时，CFG_NORM 调度下 MMAD 与排空几乎无重叠；改用 CFG_MDL 的多数据加载调度模板可让加载与计算/排空更好衔接，但 UnitFlag 的语义是 MMAD↔FIXPIPE 同步，不能据此推断 MTE1/MMAD 解耦。"
tags:
  - task.optimization
  - topic.attention
  - topic.programming_model.execution_unit.cube
  - topic.data_movement.data_copy
  - topic.memory
  - topic.tiling
status: stable
sources:
  - resource: https://gitcode.com/cann/asc-devkit/blob/639b2b5c1031188107d23d785d52b935f1b4f13b/docs/zh/guide/operator_practice/best_practices/matmul_tuning_cases/matmul_mdl_template.md
    role: primary
  - resource: https://gitcode.com/cann/asc-devkit/blob/639b2b5c1031188107d23d785d52b935f1b4f13b/docs/zh/guide/operator_practice/best_practices/matmul_tuning_cases/matmul_tiling_strategy.md
    role: supporting
  - resource: https://gitcode.com/liuyu15819/cannbot-skills/blob/f549d6d3320ac49e3e6e766600fd32bbaf37782a/cases/disc_x122.json
    role: evidence
created_at: "2026-10-28T00:00:00Z"
updated_at: "2026-10-28T00:00:00Z"
platforms:
  - a2
---

> 迁移自 cannbot-skills `plugins-community/ops-perf-evolution/skills/evolution-knowledge/references/okf/`（原 OKF v1 卡，编号 X122）。
>
> 原始元数据：
>
> ```yaml
> id: X122
> origin: discovered
> confidence: single_op
> op_families: [matmul, cube, attention, cv-mix, moe]
> bottlenecks: [no_overlap, partial_overlap, compute_bound]
> ```

> 证据：基线/变体与逐 case 数据见 [证据包 cases/disc_x122.json](https://gitcode.com/liuyu15819/cannbot-skills/blob/f549d6d3320ac49e3e6e766600fd32bbaf37782a/cases/disc_x122.json)。
> 平台说明：`a2` 对应 Ascend 910B 系列（本卡实测型号见正文）；`a3` 对应 Ascend 910C 系列。

# Strategy X122: L0C 满额单累加器时把 cube 调度 CFG_NORM 换成 CFG_MDL

## 判据（先算这一步，再谈任何带宽/tiling 手段）

```
L0C_bytes_needed = baseM * baseN * sizeof(fp32 累加器)
910B2C L0C = 128 KB
```

`baseM=128, baseN=256` → `128*256*4 = 131072 B = 128 KB`，**恰好占满整个 L0C**，只能放 1 个累加器。
（再往上 `256*256*4 = 256KB` 物理不可行——这解释了本库 F17「放大 base tile 必败」的另一半原因：
不是没放大，是真放不下。）

此时若同时观察到：

- `aic_mac_ratio` 明显低于 `aic_mte2_ratio`（本例 0.62 vs 0.878），但

且**所有带宽向手段都已打平或负向**（L2 分块、serpentine 遍历、baseK 64→128、depthB1 加深、
L2 persist hint、网格朝向翻面、`SetBufferSpace` 满额上报），那么瓶颈不在搬运，而在
**cube 内部的依赖气泡**。

## 机制（分层说明）

1. **UnitFlag 的官方语义**：`enUnitFlag` 控制 **MMAD 与 FIXPIPE 之间的 512B 细粒度同步**，
 用于让计算与结果搬运重叠；它**不是** MTE1↔MMAD 的绑定开关。因此不能把本案例的收益
 直接归因于「UnitFlag 解开了 MTE1 与 MMAD」。
2. **CFG_NORM 的调度形态**：`GetNormConfig()` 默认 `enUnitFlag = true`。在单累加器
 （`baseM*baseN*4` 占满 L0C）下，第 i 个 tile 的 K 方向累加必须整体 FixPipe 排空写 GM，
 第 i+1 个 tile 的 MMAD 才能拿到 L0C 地址 ⇒ MMAD 与「排空」之间几乎没有重叠。
3. **CFG_MDL 的改动**：`GetMDLConfig()` 默认 `enUnitFlag = false`，采用多数据加载 /
 outer-product 调度模板，L1 侧按 step 块深预取。实测收益是真实的（见下表），但**具体是哪一层
 解耦带来收益**仍需 Matmul 模板或生成指令级证据；本卡只把它记录为「调度模板改变 + profiling
 观测」，不把结论泛化为「MDL 必然解耦 MTE1/MMAD」。
4. **profiling 侧的判据**：本案例观察到 `aic_mac_ratio` 低于 `aic_mte2_ratio`，且 L2→L1 流量
 远低于峰值、所有带宽向手段打平或负向 ⇒ 瓶颈更像 cube 内部依赖气泡，而不是搬运带宽。
 注意 `aic_mte2` 对应 **GM→L1/UB** 方向的搬入，L1→L0 属 **MTE1**；若要声称 MTE1 饥饿，
 需另给 MTE1 / PipeUtilization 证据。

## 实现要点（最小侵入、可回滚）

1. tiling 结构体（host/device 共享头）尾部加 `int64 mmCfg;`（0=CFG_NORM，1=CFG_MDL）。
2. kernel：把 `GemmBody` 提成 `GemmCore<T, CFG>` 模板，`GemmBody` 读 tiling 后按 `g.mmCfg` 分发。
 **两份实例化共存**，未命中的形状执行的机器码与改动前逐字节一致，回滚只改一行。
3. host：在 `GetTiling` 之后按形状门控 `g.mmCfg = 1`。tiling 数值（baseM/N/K、step、depth）
 **一律不动**，L0C/L1 占用不变 ⇒ 不会触发 ShapeValidCheck。
4. 门控判据不是形状本身，而是**每核 tile 数**：每核要跑很多 base tile 的形状收益才大。

## 适用 / 不适用（实测边界）

- ✅ 每核 tile 多、M 方向长的 GEMM（本例 G2：`M=8192, N=24576, K=1536`，1×24 网格、每核 ~64 个
 排空气泡不被反复放大，MDL 反而多了 flag 开销。
 优先级按逐 case A/B 决定，本例保留 MDL。

## 验证状态

本卡为 `status: stable`：定量结果与运行标识见证据包 `cases/disc_x122.json`；引用时请结合上文适用条件与失效边界判断适用范围。

## 来源

来自内部进化运行；运行标识、设备、用例与逐 case 数据见证据包。
