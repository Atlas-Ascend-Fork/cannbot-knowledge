---
type: Optimization
title: "流量分档异构 AIV 核数（launch 地板 + per-core MTE 双约束下按总流量选核数）"
description: "KERNEL_TYPE_AIV_ONLY 的纯访存 elementwise 内核，核数（= blockDim）选择同时受 launch 地板与 per-core MTE 吞吐两个相反约束支配；按总流量分档选择核数，比全域统一核数更稳。"
tags:
  - task.optimization
  - topic.data_movement
  - topic.memory
status: draft
sources:
  - resource: https://gitcode.com/cann/cannbot-knowledge/merge_requests/103
    role: primary
created_at: "2026-10-13T00:00:00Z"
updated_at: "2026-11-03T16:45:00Z"
platforms:
  - a2
---

# X74: 流量分档异构 AIV 核数

## 核心思路
`KERNEL_TYPE_AIV_ONLY` 的纯访存 elementwise 内核，核数（= blockDim）选择同时受两个相反约束支配：

- **launch/派发地板项** `floor(N)`：随 N 增大而增大（每 block 的派发/回收成本）。
- **per-core MTE 项** `share(N) / BW_core`：随 N 增大而减小；AIV 侧存在 per-core MTE
  吞吐上限（L2 供数），`share = totalBytes / N`。

最优 N 是 `min_N max(floor(N), share(N)/BW_core)`，**不同流量档位落在不同的 N 上**，因此正确做法是 host 侧按总流量分档，
而不是全域统一核数：

```
totalBytes 小时（地板主导）：维持较小的核数档
totalBytes 大时（per-core MTE 主导）：用满可用 AIV
阈值落在两条曲线的交点，按目标 shape 集标定
```

实现上核数用**运行期探测**取得而非硬编码（`aclrtGetSocName()` 判 910B2* → 48，未知 SoC 回退 40），
因为同一份二进制要跑在 20 AIC/40 AIV（910B3/B4）与 24 AIC/48 AIV（910B2C）两种形态上。

## 适用场景
- **算子类型**：纯 elementwise / broadcast（每元素独立、读写字节数固定），`AIV_ONLY` 任务类型
- **瓶颈类型**：同时存在「与 shape 无关的 launch/唤醒地板」和「per-core MTE 上限」两类约束时
- **前提条件**：
  1. host 能把张量拍平为 1D 并拿到 `totalBytes`（`numel * sizeof(dtype)`），且 tiling 分档是 host 侧可改的
  2. 核数可运行期探测（或按 SoC 分档），且 tile→核映射不依赖固定核数
  3. 必须逐档验证：**地板档（小流量）用大核数会回退**

## 实现要点
- host：`usedCoreNum = (totalBytes <= TRAFFIC_GATE) ? CORE_SMALL : aivDetected`；
  `elemNum = ceil(total/blockElems)`、`tasksPerCore = ceil(elemNum/usedCoreNum)` 随核数重算；
  小流量档的 `blockElems` 分档**不要**同时放大（UB-max 整块在小流量档可能回退）
- kernel：`Process()` 的循环边界（`tileEnd` / 是否尾块）**预计算**，去掉每 tile 的整数除与分支
  （节省的是每 tile 的标量延迟，不是吞吐）
- 与 dtype 分档正交：bf16 若已合并为单 fp32 scratch，UB 预算按 14B/elem 计，可吃到更大的 `blockElems`
- **门控纪律**：核数改动的 A/B 必须在**同一时间窗口**内做固定核数对照（并发环境下 shape 级噪声大，
  跨窗口比较会把环境漂移误判为收益）

## 边界 / 否定项
- [negation] 全域统一小 blockDim 应用到有真实搬移量的 elementwise：
  每核 MTE 饱和，吞吐明显回退
- [negation] 全域统一大核数：小流量档派发项变贵，必须分档
- [negation] 与「UB-max 整块 DataCopy 合并」叠加：小流量档可能回退
  （块/barrier 数量不是本类算子的杠杆）
- 用前按上文的 `max(floor(N), share(N) / BW_core)` 在两三个流量档位标定，不要直接搬用固定的核数/阈值

## 验证方法
- **性能**：同一设备、同一时间窗口内做父变体/变体 A/B（正反序至少两轮），并保留固定核数对照；
  以绝对时延和配对差值判断，不用跨窗口比值。
- **精度**：跑全量精度用例，逐元素对比参考实现，确认分档不改变数值语义。
- **容量**：审计 UB/L1/L0C/workspace 预算（含 `blockElems` 与 fp32 scratch 的 14B/elem 估算），
  确认无越界或静默覆写。

## 补充判据（跨算子复核）

- **blockDim 16 档对齐是纯 host 一行**：`if (blockDim > 1) blockDim = max(blockDim, min(16, aivCoreNum));`。只影响 `1 < bd < 16` 的落点；空转 block 由 kernel 既有 `if (b >= batch_) return;` 立即返回，mChunks/rows/UB/描述符全不变。
- **收益在下发/调度层，不在 kernel**：某小/中 shape matmul 的同码复本净效应 +0.556/+0.698（9 条子集 -43%~-50%），全局 asc 4.3472→3.7212（**-14.4%**），kernel 二进制逐字节未变。bd=8/2/6 档全部显著慢于 16 档。
- **判据**：AIV-only 或 AIV 主导路径、bd 由 host 公式算出且经常落在 <16 的碎档；收益归因必须用同码复本配对（本机共租噪声 ±5–7%）。
- **回落闸门**：当 rows>2 等形状压缩前网格本来就能填满 16 块时，不要强行补齐；补 16 只对“碎档”有效。
