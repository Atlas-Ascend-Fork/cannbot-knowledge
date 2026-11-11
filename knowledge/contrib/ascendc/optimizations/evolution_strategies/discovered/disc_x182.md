---
type: Optimization
title: "X182: im2col 读放大 9×→1×：先改任务分解，再谈单次搬运"
description: "im2col 物化路径若按 (img, ci, kk) 逐核偏移切任务，9 个 kernel offset 各自把整张 xpad plane 读一遍，读放大 9×；此时优化的第一优先级是改任务分解为 (img, ci)-major，一次载入 plane 后用 Gather 提取 9 个窗口，而不是去省一次 GM 往返或优化单次搬运。"
tags:
  - task.optimization
  - topic.data_movement
  - topic.compute.composite
status: draft
sources: []
created_at: "2026-11-05T00:00:00Z"
updated_at: "2026-11-05T00:00:00Z"
platforms:
  - a2
  - a3
---
# X182: im2col 读放大 9×→1×：先改任务分解，再谈单次搬运

## 现象

卷积/attention 融合算子的 im2col 物化路径，常见任务分解是 `(image, channel, kernel_offset)`：每个任务负责一个 (img, ci) 和一个 `kk`（k×k 卷积的某个偏移），各自把整张 `xpad` 平面读进 UB，再写到 `bmat` 的第 kk 行。

对 k=3 的卷积，同一张 xpad 平面会被 9 个 kk 任务各读一遍——**读放大 9×**。此时 GM 流量不是“多了一次往返”，而是同一份输入被读了 9 次；单次搬运效率再高也救不回来。

## 根因

- 任务分解的最小单位是 `(img, ci, kk)`，而 xpad 平面的复用维度是 `(img, ci)`；分解粒度比复用粒度更细。
- 每个 kk 任务独立执行“载入 plane → 提取窗口 → 写 bmat 行”，plane 的载入没有跨 kk 复用。
- 物化 bmat 的写带宽是必要成本；可消掉的是 **xpad 的 9× 读**，不是 bmat 的写。

## 判据

1. 先算读放大倍数：`总 GM 读字节 / 唯一输入字节`。若接近 `k×k`（如 9×），优先改任务分解，而不是优化单次 DMA 或省一次物化。
2. 看每个任务的输入是否是同一张平面的不同偏移；若是，说明 plane 级复用可行。
3. 把“消一次 GM 往返”的预期收益与“消 9× 读放大”对比：前者通常只有 0.3% 量级（噪声），后者可达 30% 量级。

## 实现要点

1. 任务分解改为 `(img, ci)`-major：一个任务把 xpad plane 读入 UB 一次，然后用 Gather（或等价窗口提取）生成 k×k 个窗口，复用写 `bmat` 的 9 行。
2. 保持 `bmat` 的既有布局与下游 GEMM 的读法不变；只改 im2col 的任务划分和窗口提取方式。
3. 如果同一输入在多个阶段被分别 im2col（例如 stage1 与后续 conv 分支都要 im2col(x)），进一步考虑把其中一部分 GEMM 预先算成部分和并复用，避免每个阶段各做一次 im2col。
4. 读放大修复后，再评估 GEMM 侧的 BLOCK_M/操作数重读优化；顺序反了会被 im2col 瓶颈掩盖。

## 边界

- xpad plane 必须能放进 UB；放不下时要分块，但分块仍应保持 `(img, ci)` 内的 plane 复用。
- Gather 窗口提取的指令数不能超过省下的 DMA；窗口很小或 k 很小时要实测。
- bmat 的写带宽是不可消的剩余成本；读放大修复后，瓶颈会转移到写/GEMM。

## 实测证据

- 在一个 CV 融合 attention 算子中，im2col 由 `(img, ci, kk)` 改为 `(img, ci)`-major 后，单图 xpad 读从约 816MB×8 ≈ 6.5GB 降到约 90MB/图，几何平均 **+30.5%**，远超预期的 2-6%。
- 同算子中“消掉一次 Qg GM 往返”的收益只有约 **0.3%**（噪声级），说明材料化往返不是主瓶颈，读放大才是。
- 同一输入被两个阶段重复 im2col 时，把部分和预计算并复用，再得约 **+2.4%**。

## 关联

- 物化/融合：[P129](../cards/p129_fused_img2col_loaddata3d.md)（Fused img2col LoadData3D）、[X18](disc_x18.md)。
- 共享输入：[X55](disc_x55.md)（Shared-im2col 双分支）。
- 归约轴递延：[X96](disc_x96.md)（kd-defer）。
- 搬运块数 KPI：[X95](disc_x95.md)。
