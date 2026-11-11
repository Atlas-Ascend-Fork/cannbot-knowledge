---
type: Optimization
title: "X141: CV 环 per-iteration 恒定成本诊断法"
description: "把每个 shape 的墙钟除以 ring 迭代数；若该值在一批 shape 上近似恒定，说明限速点是每迭代一次的固定串行链，而不是算力、带宽或 tile 工作量。此时加深环、削 AIC 标量指令、削 AIV 向量 op 往往中性；应改为让每迭代做更多活，或让每 score 搬更少字节。"
tags:
  - task.optimization
  - task.debugging
  - topic.data_movement
status: draft
sources: []
created_at: "2026-10-28T02:30:00Z"
updated_at: "2026-11-02T17:16:09Z"
platforms:
  - a2
  - a3
---
# X141: CV 环 per-iteration 恒定成本诊断法

## 核心思路
CV 融合 ring（AIC 出 S/P，AIV 算 softmax，AIC 出 O，AIV rescale）调优时，先做一个成本很低的判据：

**把每个 shape 的 wall-clock 除以该 shape 的 ring 迭代总数**（迭代数 = 按 kernel 自己的 `kv_end` 公式逐 task 求和，再除以核数）。

若该 per-iteration 成本在一大批 shape 上**近似恒定**（跨 block_m、dim、BLOCK_N 的不同档位），则提示限速点可能是"每迭代一次"的固定串行链，而不是算力、带宽或 tile 里的工作量。这是诊断假设，需用干预实验确认：若"削减每迭代指令/向量 op/握手深度"的改动都无效，而"每迭代做更多活"或"每 score 搬更少字节"有效，假设才成立。

反例：若 per-iteration 随 tile 尺寸明显变化，则属于带宽或算力受限，应按常规 roofline 处理。

## 适用场景
- CV 融合 attention / CV 混合算子的性能诊断（AIC 产中间量经 GM 交给 AIV 消费）。
- 需要能按 kernel 的 `kv_end` 公式估算迭代总数；causal 时迭代数随 s_blk 斜坡变化，要逐 task 求和。

## 实现要点
1. **迭代数统计要按核均摊**：先按 task 求 `kv_end` 总和，再除以实际参与核数。否则不同 shape 的核利用率差异会污染 per-iteration 值。
2. **三类"看似合理但常无效"的干预**（先用判据排除，不要直接投入）：
   - **加深环**：RING/PRELAUNCH 增加的那一圈若在流水末尾、不含 stage，通常是零成本。
   - **削 AIC 标量指令**：布局外提、递增指针、`%` 改位与、epilogue 去逐行 GetValue，可能全线中性。`aic_scalar_ratio` 接近 1 往往是把 `WaitFlag/CrossCoreWaitFlag` 的阻塞计入了标量忙碌，而不是发射条数受限（见 X163/X176）。
   - **削 AIV 向量 op**：即使 `aiv_vec_ratio` 明显下降，墙钟也可能不变——AIV 可能本来就被隐藏。
3. **有效的杠杆**：增大 block_m（每迭代多算行）、增大 BLOCK_N（在容量允许时减少每 score 的 K/V 字节）、改善任务/代价序调度（消除跨核不均）。
4. **副作用警示**：破坏既有的一处 overlap 可能带来明显回退；"重叠"本身是稀缺资源，不要为了少一条 op 去破坏它。

## 验证方法
- 画 `per-iteration 成本 vs shape 参数` 的散点；恒定性是最强信号。
- 对每个候选干预，同时记录"目标 pipe 比例"和"墙钟"；只有两者同向下降才说明该 pipe 在临界路径。
- 同设备同窗口交错 A/B，至少两轮正反序。

## 关联
- 与 [X163](disc_x163.md)、[X176](disc_x176.md) 共同覆盖"scalar 比例高不等于发射受限"的判定。
- 与 [X149](disc_x149.md)（block_m 取满 L0C）是"让每迭代做更多活"的具体落地。
