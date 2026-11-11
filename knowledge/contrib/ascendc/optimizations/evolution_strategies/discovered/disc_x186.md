---
type: Optimization
title: "X186: 语义级快速路径剥离独立 kernel——主路径位级不变，共享路径不加分支"
description: "当参考实现的某类语义子集允许 O(Sq·Skv·d) 退化为 O(Skv·d) 时，把该子集剥离成独立 AIV-only kernel，host 命中时直接 launch；共享路径删除该分支并还原到位级一致。把分支加在共享路径里会污染非命中 case（实测净 -4.2%）。"
tags:
  - task.optimization
  - topic.implementation.kernel_launch
  - topic.attention
status: draft
sources: []
created_at: "2026-11-05T00:00:00Z"
updated_at: "2026-11-05T00:00:00Z"
platforms:
  - a2
  - a3
---
# X186: 语义级快速路径剥离独立 kernel——主路径位级不变，共享路径不加分支

## 核心思路

三步：

1. **语义识别**：从参考实现读出可特化的数学等价。例如某些 mask/band 语义子集下，输出退化为 `mean(V[:E])`，计算量从 `O(Sq·Skv·d)` 降到 `O(Skv·d)`。识别要读 mask 语义，而不是只按 shape/md5 表做特判。
2. **隔离剥离**：快速路径做成独立 AIV-only kernel（独立 Kernel 类 + 最小 tiling 结构），host 命中时直接 launch。**共享路径必须还原**：去掉分支、还原 tiling 结构、去掉多余入参，保持位级一致。
3. **内部再优化**：剥离后的核仍有自己的瓶颈链——流式前缀累加去 V 重读、kv-head 并行度坍缩时门控回退、BSH 布局读写双修等。

## 判据

1. 存在可证明的数学退化（uniform mean、恒等矩阵、单位阵上采样、恒等跳过 GEMM 等），且命中 case 的绝对耗时可观。
2. 语义 gate 的覆盖面 > 形状/md5 特判：按 mask 语义判定通常能覆盖更多 case（实测语义 gate 覆盖 30 个 case，md5 表只覆盖 9 个）。
3. 主路径流量必须可还原到位级一致；做不到就不要走剥离路线，改用正交优化。

## 实现要点

1. 独立 kernel 只保留该语义子集需要的最小 tiling/入参，避免把主路径的通用结构带进去。
2. host 侧按语义 gate 命中直接 launch；未命中走原主路径，主路径不加任何分支。
3. 反例：把分支塞进共享路径会带来三类污染——每任务分支判断（打断软流水）、tiling 膨胀（如 80B→212B）、多余入参；实测让 41 个非命中 case 回归约 12%，净 **-4.2%**。
4. 剥离后再做内部优化；不要把“命中 case 快”与“主路径无回归”混在一起归因。

## 边界

- 只有数学退化可证明时才适用；不能只凭“某些形状看起来简单”就特化。
- 命中 case 很少或绝对耗时很小时，独立 launch 的固定成本可能吃掉收益。
- 主路径无法还原到位级一致时，不要做语义剥离；用 X185/X187 这类正交优化替代。
- 语义 gate 必须覆盖真实输入契约；用 md5/shape 表做 gate 容易漏掉同语义的不同形状。

## 实测证据

- 把 band-mean 快速路径放在共享路径：9 个命中 case 快 24%，但 41 个非命中 case 回归 12%，**净 -4.2%**。
- 剥离为独立 AIV-only kernel、主路径位级一致：命中 case **1.68–3.24x**，非命中零回归。
- 语义 gate 替换 md5 表（覆盖 9+11+10=30 个 case）：**1.7210x**（+36.8% vs champion）。
- 剥离后 per-kv-head 流式累加 + 并行度门控：1.7916→1.8218x；全 mask 语义子集（`O(Sq·Skv·d)→O(Skv·d)`）1.085x。
- 同型案例：恒等跳过 GEMM（`ks==3` 单位阵）3.59x。

## 关联

- 形状自适应双引擎：[X13](disc_x13.md)。
- 路由选中分支消除：[X42](disc_x42.md)。
- 稀疏/稠密双路径：[P62](../cards/p62_sparse_dense_dual_path_dispatch_dra.md)。
- Stage/barrier 消除：[X77](disc_x77.md)。
