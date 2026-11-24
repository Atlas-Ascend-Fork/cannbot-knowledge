---
type: Optimization
title: 连续源列窗搬入 UB，再由 SIMT 完成逐元素 gather
description: 把全部源行的连续列窗搬入 UB，跨输出索引行复用，再由 SIMT 按索引读取并写回。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.implementation.pipeline
- topic.data_movement
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/compact-source-window-simt-gather.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- '950'
---

<!-- strategy-metadata
{"id":"COMPACT-SOURCE-WINDOW-SIMT-GATHER","slug":"compact-source-window-simt-gather","classification":"validated_strategy","generality":"op_class","created":"2026-11-09","operator_class":"index-gather","related_strategies":["t2-small-xdim-slab-bulk-mte2-simd-gather"],"evidence_policy":"具名来源与测量单独归档，不作为通用分派阈值。"}
-->

# 连续源列窗搬入 UB，再由 SIMT 完成逐元素 gather

> 单一优化方向：改变随机源读取的位置。按源轴的全部行装入紧凑列窗，在 UB 中按索引取值，跨输出索引行复用同一源窗口。

## 原理与适用条件

对 `y[o,r,j] = x[A(o)+index[o,r,j]*S+j]`，若同一外层坐标下源行步幅 `S` 固定，且末端坐标 `j` 在源和输出中均连续，可以取 `W` 列作为窗口，把全部 `G` 个源行对应的列搬入 UB。SIMT 再按每个输出位置的索引读取片上源窗。索引仍可完全乱序，优化依赖的是多个输出索引行复用同一列窗。

适用前提是能从合法 shape、步幅和类型推导连续列窗，并且全源行窗口、索引块及并存临时空间都放得下。源窗装入的是整个合法索引域，并不只装当前索引中已经出现的行。若源轴过大只能切出很窄的窗口，或者直接读本已接近连续、输出行间又缺少复用，应优先保留原访问路径。

本策略与[小源轴分片搬运](t2_small_xdim_slab_bulk_mte2_simd_gather.md)共享连续搬入的思路。这里的消费者是 SIMT，片上地址表示、搬运到消费的依赖以及尾窗处理都要按实际实现检查。

## 正确性红线

- 分别证明 GM 源地址、UB 行距与输出地址。窗口内地址按实际 UB 行距计算，尾窗逻辑宽度、DMA 补齐宽度和消费者物理读宽不能混用。
- 2D DMA 的块长、源/目的跨步和单位按当前 API 核对。超过描述符字段范围时拆成合法搬运，保证分段起点对齐、源行覆盖完整、目的写入不重叠。
- 源窗及索引块写完并对消费者可见后才能读取。复用缓冲前等待消费结束；若使用双缓冲，分别核对两套存储的占用和依赖。
- 保持索引的解释、边界行为和输出所有权。纯复制保持浮点及整型位模式；不满足外层仿射或内层连续条件的形状走经过验证的通用路径。

## 实施与代价

1. 写出源窗实际字节预算：`G × UB行距字节数`，再加索引块、对齐保护区和其他并存缓冲。由可用容量和搬运粒度推导窗口宽度、索引块行数及尾窗方案。
2. 按 `(外层坐标, 列窗)` 划分不重叠的输出任务。每个任务先装入源窗，再分批搬入索引、消费源窗和写回。分核时比较复用量与任务数，避免为了切更多任务反复装入同一源窗。
3. 计入搬入未被索引命中的源元素、描述符、等待、片上存储和索引搬运成本。比较改造前后的完整调用；仅凭随机读变成连续搬运，不能推出流量一定下降。
4. 用重复索引、遍及全源行的乱序索引、满窗与尾窗、描述符边界及连续调用验证。用实际目标域和未命中域定门槛，减少有效复用或并行度时保留原路。

## 检索卡（短卡）

动作：把全部源行的连续列窗搬入 UB，跨输出索引行复用，再由 SIMT 按索引读取并写回。
适用：源行步幅固定、列方向连续，源窗与索引块放得下，且跨输出行可复用。
限制：核对源与 UB 行距、DMA 单位及尾窗；搬入完成后才消费，读完才复用，保持原索引语义。
范围：逐元素索引收集的数据搬运与片上访问。
检索词：源列窗、SIMT、UB 索引、二维搬运、连续搬入、尾窗。
机会：随机源读转为连续搬入，同一源窗由多行输出复用。
代价：搬入未命中元素、UB 占用、描述符与等待；复用不足时可能回退。
