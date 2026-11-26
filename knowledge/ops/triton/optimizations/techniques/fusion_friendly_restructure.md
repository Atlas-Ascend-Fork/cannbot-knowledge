---
type: Optimization
title: 可融合重构（单 launch 契约下的结构改造）
description: 融合失败时的可融合重构：判断阶段边界归属（行内阶段就地完成还是拆给别的 program）、中间量布局（按消费方收缩轴 chunk-major，避免物化转置）、阶段间交接（常驻 grid、cube/vector/sub-vector 逐类屏障、连续整 tile 写入与尾块补齐，scatter_add 稀疏更新在生产者片上合并重复索引，避免消费者读取旧中间量）；给出五步重构流程与 P=1/P=核数 稳定性验证。
tags: [task.optimization, topic.implementation.pipeline, topic.memory, topic.data_movement]
status: stable
sources:
- resource: https://gitcode.com/Ascend/triton-ascend/blob/c22984baa55e1506eadd7c72955d9bf669b1c959/docs/zh/triton_api/Extension_Ops/sync_block.md
  role: primary
created_at: '2026-11-22T00:00:00Z'
updated_at: '2026-11-22T00:00:00Z'
platforms: [a2, '950']
---
# 可融合重构（单 launch 契约下的结构改造）

多 kernel 基线为了单阶段性能，常采用“每阶段一个 kernel + 阶段间 GM 往返”的结构。这种结构直接融成单 launch 时，往往不是“barrier 没调好”，而是**结构本身不可融合**。本卡给的是融合失败时先做的一次结构改造，不是流程门禁。

## 触发条件

单 launch 契约下融合失败，且现象属于以下之一：

- 消费方读到未完成的中间量：`P=1` 精确、`P` 增大后 run-to-run 误差非确定（跨 program 可见性问题）；
- 单 kernel 内累加器放不进 UB，必须把 tile 压到不可用的尺寸；
- 为了进入 dot 的 fast-form 而物化转置副本，单 kernel 里无法消除该副本与其工作区。

## 三个可融合结构条件

1. **行内阶段就地完成**：scatter、归一化、按行缩放这类只依赖本行数据的阶段，由**写这一行数据的同一个 program** 就地 `load → 改 → store` 完成；不要拆成独立 phase 交给别的 program（一旦拆开就引入跨 program 依赖，需要单独验证阶段间数据交接，见 `sync_and_barrier.md`）。
2. **中间量按消费方收缩轴分块存储**：把中间量按 `[NV][M][VC]` 这类 chunk-major 布局写，使两个 consumer 的收缩轴都落在连续方向（fast-form），从结构上消掉物化转置与转置工作区。
3. **按执行单元验证交接**：混合 cube/vector 的阶段使用与参与执行单元匹配的逐类屏障。对常驻 grid，按物理核数分派 program，各阶段由同一批 program 遍历 tile，所有参与者按同一顺序到达屏障。共享工作区优先用连续整 tile 写入，尾块分配 padding，消费端屏蔽无效元素。屏障与写入形态要组合验证（见 `sync_and_barrier.md`）。对 logits → scatter_add → GEMM，优先让每个 logits tile 的生产者按 tile 列范围筛选 top-k 更新，在片上对重复目标求和并完成参考精度转换，再连续写出整块最终中间量。这样消费者只跨阶段读取整块，无需等待对同一 GM 中间量的稀疏改写。按 tile 复用行级索引，测量 K 扫描及 UB 占用；复验重复索引、尾块、满核交接和真实 shape 性能。

## 重构步骤

1. **画依赖图**：列出每个阶段“写哪些 GM 区域、读哪些 GM 区域”，标出每一条跨 program 边。
2. **消边**：跨 program 边优先改成 row-owner 归属（写者与读者同一 program）或本地重算；无法消除的累积型输出改 `atomic_add`（可交换、无需读数）。
3. **定中间量布局**：按第 2 条条件选 chunk-major，并让两个 consumer 的 tile 直接对齐该布局，避免额外转置 kernel。
4. **交接验证**：先 `P=1` 确认逐 tile 正确，再用满核 grid 重复测试。用每轮不同的数据和 NaN 哨兵区分旧值、未写入与数值误差；分别检查 producer→consumer、scatter 后读取、跨 chunk 累加与工作区复用。若首个 consumer 读到旧值，再检验消费者顺序及编译后的预取位置。
5. **再测性能**：重构后逐阶段与多 kernel 基线对比；只有重构后仍不达标才回到“换交换协议”或“放弃融合”的决策。

## 常见错误速查

| 现象 | 原因 | 做法 |
|---|---|---|
| `P=1` 对、`P>1` 错乱 | 参与者未到齐、写入尚不可见或读取被提前 | 消边（row-owner/重算）；仍需交换时，分别验证到达、整 tile 写入与读取顺序 |
| 单 kernel 里 UB 溢出 | 单 program 持有整个输出的累加器 | 改 `atomic_add` 到 GM，或用 `atomic` 累加器替代 UB 累加器 |
| 单 kernel 反而慢很多 | 融合导致 tile 缩小、流水深度降级 | 先按本卡重构；仍慢则保留多 kernel 交付并记 fusion tax |
| 多出转置 kernel / 转置工作区 | 中间量按行主序存，consumer 收缩轴不连续 | 改 chunk-major 存储，让 consumer 直接 fast-form |

## 参考

- 同步语义与跨核可见性：`sync_and_barrier.md`
- 融合收益与 fusion tax：`operator_fusion.md`
- 上游同步 API：`https://gitcode.com/Ascend/triton-ascend/blob/c22984baa55e1506eadd7c72955d9bf669b1c959/docs/zh/triton_api/Extension_Ops/sync_block.md`
