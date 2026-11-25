---
type: Optimization
title: "X118: 归约向量重复读摊薄 + split-K 折叠"
description: "纯 AIV 多段流水里，fp32 中间向量在归约段被按行重复读往往是一阶成本；用行块摊薄重复读、split-K 折叠与末段降维，可把归约从标量壳改成块操作。"
tags:
  - task.optimization
  - topic.attention
  - topic.programming_model.execution_unit.cube
  - topic.programming_model.execution_unit.vector
  - topic.data_movement.data_copy
  - topic.memory
status: stable
sources:
  - resource: https://gitcode.com/cann/asc-devkit/blob/639b2b5c1031188107d23d785d52b935f1b4f13b/docs/zh/api/SIMD-API/adv_api/reduction_operations/ReduceSum_interface/ReduceSum.md
    role: primary
  - resource: https://gitcode.com/cann/asc-devkit/blob/639b2b5c1031188107d23d785d52b935f1b4f13b/docs/zh/guide/operator_practice/simd_operator_optimization/memory_access/reduce_non_contiguous_transfer.md
    role: supporting
  - resource: https://gitcode.com/liuyu15819/cannbot-skills/blob/f549d6d3320ac49e3e6e766600fd32bbaf37782a/cases/disc_x118.json
    role: evidence
created_at: "2026-10-27T00:00:00Z"
updated_at: "2026-10-27T00:00:00Z"
platforms:
  - a2
---

> 迁移自 cannbot-skills `plugins-community/ops-perf-evolution/skills/evolution-knowledge/references/okf/`（原 OKF v1 卡，编号 X118）。
>
> 原始元数据：
>
> ```yaml
> id: X118
> origin: discovered
> confidence: single_op
> op_families: [reduction, elementwise, attention, cv-mix]
> bottlenecks: [mte2_stall, undersize_transfer, scalar_compute, tiling_imbalance]
> ```

> 证据：基线/变体与逐 case 数据见 [证据包 cases/disc_x118.json](https://gitcode.com/liuyu15819/cannbot-skills/blob/f549d6d3320ac49e3e6e766600fd32bbaf37782a/cases/disc_x118.json)。
> 平台说明：`a2` 对应 Ascend 910B 系列（本卡实测型号见正文）；`a3` 对应 Ascend 910C 系列。

# Strategy X118: 归约向量重复读摊薄 + split-K 折叠

## 核心思路

纯 AIV 多段流水里，真正的一阶成本常常不是那个「大张量」，而是**几个 fp32 中间向量在归约段被按行重复读**。

判据（先算账，再动手）：设 x 为 (b, c, n)，某个 fp32 归约向量 v 为 (b, n)。
若归约段按「一个 (b,c) 行一个 task」组织，每个 task 都要读整条 v[b]，则

```
v 流量 = c × (b·n·4B) 而 x 流量 = b·c·n·sizeof(T)
=> v 流量 / x 流量 = 4 / sizeof(T) // fp16/bf16 时 = 2 倍！
```

（同一结论由本轮另外两个变体独立推出：一个从搬运账、一个从事务账，互不引用。）

## 适用场景

- 纯 AIV 多段流水（通道注意力 / SE / 门控 / GEMV 链 / per-channel 归一化），
 且存在 fp32 中间向量喂给沿大轴的归约；
- 判据（三条任一）：某段「时间占比高 + 有效带宽低一个数量级」；kernel 出现
 `for c: <读一整条 fp32 向量> → ReduceSum → GetValue`；某段 grid 表达式含 `b*ceil(n/NB)` 之类「小 n 时退化成 b」的形态。

## 实现要点

1. **通道块瓦片摊薄重复读**：task 从「1 行」改成「R 行（R=8~16）通道块」，一个 v 列块喂 R 行 → 重复读 ÷R；
 行和用 `ReduceSum(pattern=AR)` 一次产出 R 个值、整块 StoreSeg 写回（顺带消掉逐行标量壳）。
2. **沿归约轴 split-K + 极小 combine**：按 (b, 列块, 通道切片) 三维派任务，各片写 fp32 部分和再折叠；
 `csplit == 1` 时直接出终值、不发 combine（否则给最小 case 加固定 launch 地板）。
3. **末段降维成纯逐元素流**：`out = sigmoid(Σ_c wt[c]x[c,:] + bc) ⊙ w ⊙ x` 拆成 rowgemv（只写 b·n 小量）
 + elem_out（单遍读 x 写 out），x 从 3 份流量降到 2 份。

## 陷阱

- **列块宽度双刃**：列块取窄（512）让行 burst 只有 1KB，大 n 时 MTE2 事务数涨 8 倍，
- **fp32 部分和要预清零，或让写者独占输出列块**，否则多任务写同一段部分和互相覆盖。
- **combine kernel 是固定开销**，小 shape 上多发一次 launch 可能比省下的时间更贵。

## 验证状态

本卡为 `status: stable`：定量结果与运行标识见证据包 `cases/disc_x118.json`；引用时请结合上文适用条件与失效边界判断适用范围。

## 来源

来自内部进化运行；运行标识、设备、用例与逐 case 数据见证据包。

## 本轮补充（与 X119 合流，已验证）

在 X118 的三刀之上，本轮把「列块宽度」这条陷阱量化成了可执行的规则（详见 X119）：
`W = min(n, 8192/sizeof(T))`（fp16/bf16→4096、fp32→2048），每笔 burst 落进 2~8KB；
并用「块内偏移折进 `j % 512` 槽」把 fp32 累加器与块宽解耦，使宽 burst 不必配 `rows×width` 累加器。

同时否证了两条：
- **M=1 GEMV 不要交给 Cube**（P102）：硬件计数 `aic_mte2_ratio 0.748 / aic_mac_ratio 0.079` 证明该形态是带宽墙，
 且 Cube 要求 A/B 同 dtype，会把 fp32 融合权重逼成 bf16 而破坏精度（见 OKF failure-pattern F18）。

## 问题现象

流量账一眼看穿：α 是 fp32 (b,n)，`chan_reduce` 按「一个 (b,c) 行一个 task」组织，每 task 重读整条 α[b] ⇒

```
α 流量 = c · b·n·4B x 流量 = b·c·n·sizeof(T)
```

也按 batch 口径测得。引用时应与变体使用同一参考口径，并注明所选口径。

## 有效范围与陷阱

- 适用于：纯 AIV 多段流水，且存在 fp32 中间向量喂给沿大轴的归约（通道注意力 / SE / 门控 / GEMV 链 / per-channel 归一化）。
- **部分和必须预清零或写者独占输出列块**，否则互相覆盖（首次实现即此错）。