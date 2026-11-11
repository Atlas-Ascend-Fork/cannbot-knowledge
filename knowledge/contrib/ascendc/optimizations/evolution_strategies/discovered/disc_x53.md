---
type: Optimization
title: "X53: 批量 2D online softmax（跨 head-group 向量化，热循环 0 标量）+ 自适应 head-group tiling"
description: "decode/GQA/MLA 类 attention 内核的 online softmax 若按 per-head 逐 block 处理，每个 row-block 每 head 要做 ReduceMax/ReduceSum+GetValue 与 ScalarExp，scalar pipe 容易成为主导瓶颈。把 [G,bw] 组内多 head 一次整体归约与 rescale，使热循环 GetValue 降为 0；host 侧按 B 与 AIV 核数自适应选择 head-group 大小以填满核。"
tags:
  - task.optimization
  - topic.attention
  - topic.compute.normalization
status: draft
sources:
  - resource: https://gitcode.com/cann/cannbot-knowledge/merge_requests/103
    role: primary
created_at: "2026-10-13T00:00:00Z"
updated_at: "2026-11-03T16:45:00Z"
platforms:
  - a2
---

# Strategy X53: 批量 2D online softmax（跨 head-group 向量化，热循环 0 标量）+ 自适应 head-group tiling

## 核心思路
decode/GQA/MLA 类 attention 内核的 online softmax 若按 **per-head** 逐 block 处理，每个 row-block 每 head 要做 ReduceMax[1,bw]+GetValue、ReduceSum[1,bw]+GetValue、ScalarExp → scalar pipe 是主导瓶颈（profiling 上表现为 scalar_ratio 高）。两个杠杆：
1. **批量 2D online softmax**：把 [G,bw]（G=组内 head 数）一次整体 ReduceMax→[G,1]、exp 全向量、ReduceSum→[G,1]，online rescale 全部用 [G] 小向量 Max/Exp/Mul 完成，热循环 GetValue 从 G×2~3 降到 **0**，scalar pipe 空闲。
2. **自适应 head-group tiling（host）**：固定 hg=min(H,8) 时大 kv 小 B 的 case 只有少量 block（严重欠核）；host 按 B 与 AIV 核数动态选最小 hg（≥1，ckv 跨 head 读放大 ≤2x）使 `numBlocks=B*ceil(H/hg) ≤ aivCoreNum` 且尽量填满，提升低并行 case 的核利用率。

## 适用场景
- decode 场景的 GQA / MLA / Paged attention（H 个 head、每 head 各自 QK/PV，online softmax 串行 rescale）
- scalar_loading 高的 online softmax（scalar_ratio 显著偏高，如 > ~0.3）
- 低并行度 case（B*H ≤ AIV 核数，固定 hg 导致 block 数 < 核数）
- 与 P119（两遍→online softmax）互补：P119 解决"是否 online"，X53 解决"online 后如何把 rescale 向量化 + 如何填核"

## 实现要点
1. 批量 softmax：`ReduceMax[G,bw]→[G,1] mBlockVec`；`eArr=exp(scores-broadcast(mBlock))*valid` 全向量；`ReduceSum[G,bw]→[G,1] sumEVec`；rescale：`mNew=max(mOld,mBlock)`；`p_old=exp(mOld-mNew)`；`p_new=exp(mBlock-mNew)`；`accO[G,dc]*=p_old`；`eArr*=p_new`；`larr=larr*p_old+sumE*p_new`（全部 [G] 小向量 Max/Exp/Mul，0 个 GetValue）。
2. 自适应 hg：host 遍历候选 hg 从 1 起，满足 ckv 读放大 ≤2x 且 `B*ceil(H/hg) ≤ aivCoreNum` 的最小值，尽量把核填满；读放大上限防止 memory-bound 时流量翻倍亏本。
3. G=1 精简路径：H=1 或小 H 时走轻量标量路径，避免 [1,bw] 2D 广播向量开销。
4. 陷阱：eArr 已按全局 max 归一化后**不得二次 rescale**（重复 rescale 会导致 H=1 精度错）；去 PIPE 屏障需谨慎（可能引发 NaN 竞态，需回退保正确）。

## 验证方法
- 在目标算子上做同设备同窗口 A/B（正反序至少两轮），比较父变体与变体；用全量精度门禁与逐 bit/逐元素对比确认语义未变。
- 容量类改动先做 UB/L1/L0C 预算审计；诊断类改动先做同码 A/A 噪声带。
