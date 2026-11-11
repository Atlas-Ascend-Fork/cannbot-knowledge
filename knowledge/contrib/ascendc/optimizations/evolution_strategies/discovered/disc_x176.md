---
type: Optimization
title: "X176: AIC scalar 高占用是等待阻塞，不是发射条数"
description: "CV 融合环里 aic_scalar/aiv_scalar 常年接近饱和，容易被误判为标量发射受限。用敏感性探针（每 tile 插入自配对 flag）和全量编译期特化两组对照可证伪：若插入指令只带来噪声级变化、特化后比例与时长都不动，则比例主体是 WaitFlag/CrossCoreWaitFlag 的阻塞周期。正确杠杆是缩短 S/P 依赖链，而不是削标量指令。"
tags:
  - task.debugging
  - task.optimization
  - topic.architecture
status: draft
sources: []
created_at: "2026-11-02T16:31:31Z"
updated_at: "2026-11-02T17:16:09Z"
platforms:
  - a2
  - a3
---
# X176: AIC scalar 高占用是等待阻塞，不是发射条数

## 核心思路
CV 融合环里 `aic_scalar` / `aiv_scalar` 常年接近饱和，很容易被误判成"标量发射受限"。但 scalar 比例统计的是**标量管有周期在跑**，`WaitFlag` / `CrossCoreWaitFlag` 阻塞期间也算忙。用两组独立对照可以证伪"发射条数受限"：

1. **敏感性探针**：在每个 AIC ring 迭代额外插入若干对自配对 `MTE1_MTE2` flag（足以制造可观测的指令增量），输出仍正确。若墙钟只变化到噪声级，说明标量管还有余量，比例高不是指令吞吐造成的。
2. **全量编译期特化**：把 tiling / stride / 循环边界 / 任务解码 / mask 分支全部折叠为常量（独立入口，并用 msprof 确认实际执行的是特化版本）。若 `aic_scalar` 比例与 kernel 时间都不动，进一步证明比例主体是等待。

结论：该比例的主体是 **WaitFlag/CrossCoreWaitFlag 的阻塞周期**（依赖链等待），不是指令数。判定时要同时看"比例是否下降"和"时长是否下降"：比例降而时长不降 = 该 pipe 不在临界路径。

## 适用场景
CV 融合环 + GM workspace 交接的 kernel，且 aic_scalar/aiv_scalar 接近饱和、需要判断是等待阻塞还是发射条数时。

## 证据形态
- 插入 flag 指令只带来噪声级变化。
- 全量特化后 scalar 比例几乎不动，kernel 时间也不动。
- AIV 侧同样可能被隐藏：删除整条 P 生产链（Muls+mask+Exp）只快很少；删 l 链无收益。
- ring 深度改为非 2 的幂可能因 modulo 增加标量开销而变慢，不能证明"加深有效"。

## 边界与失效条件
- 适用于 CV 融合环 + GM workspace 交接（S/P 往返）的 kernel；纯向量/纯 cube 不适用。
- 不能因为 scalar 高就加 flag/等待对；这会增加指令但不缩短链。
- 缩短链的可行方向：head-major K/V（X173）、减少 S/P 链跳数、增大每跳工作量（容量允许时）。

## 验证方法
- 7-metric PipeUtilization + 两个阳性对照（加 flag、全量特化）。
- 同场 A/B（同一测试工具、同一设备窗口），正反序多轮。
- 输出逐 bit 对比，确认探针没有改变数值。

## 关联
- 与 [X141](disc_x141.md)（per-iteration 恒定成本诊断）和 [X163](disc_x163.md)（三族证伪）互为补充；三张卡从不同实验角度得到同一结论。
- 与 [X173](disc_x173.md)（head-major K/V）是"缩短依赖链"的具体落地。
