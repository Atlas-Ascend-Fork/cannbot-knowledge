---
type: Optimization
title: "流量分档异构 AIV 核数（launch 地板 + per-core MTE 双约束下按总流量选核数）"
description: "KERNEL_TYPE_AIV_ONLY 的纯访存 elementwise 内核，核数（= blockDim）选择同时受两个相反约束支配："
tags:
  - task.optimization
  - topic.data_movement
  - topic.memory
status: draft
sources:
  - resource: https://gitcode.com/cann/cannbot-knowledge/merge_requests/103
    role: primary
created_at: "2026-10-13T00:00:00Z"
updated_at: "2026-10-13T00:00:00Z"
platforms:
  - a2
---

# X74: 流量分档异构 AIV 核数

> 进化发现元数据（迁移自 cannbot-skills `references/discovered/` 原始 frontmatter）：
>
> ```yaml
> schema_version: okf.v1
> kind: discovered_strategy
> id: X74
> title: "流量分档异构 AIV 核数（launch 地板 + per-core MTE 双约束下按总流量选核数）"
> origin: discovered
> discovered_round: 2
> discovered_from: "Exp evolution, round_2/parallel_1 (node n6, strategy_guided; 由 round_1 对 48-AIV 全域铺开的证伪反向导出)"
> base_speedup: "geomean 4.9254x -> 5.0036x vs PyTorch（同窗口基线等价体 4.8621x，+2.9%）；mid 档 case2 -12.9% / case12 -17.6% / case8 -15.2%（3 次复现）；20/20 精度"
> confidence: single_op
> status: active
> op_families: [elementwise, broadcast]
> bottlenecks: [tiling_imbalance, no_overlap, mte2_stall]
> tags: [blockdim, core-count, launch-floor, per-core-mte, traffic-gated, heterogeneous-policy, elementwise, 910b2c, dav-c220, aiv-only]
> strategy_ids: [X74, P112, P2, P54]
> ```

## 核心思路
`KERNEL_TYPE_AIV_ONLY` 的纯访存 elementwise 内核，核数（= blockDim）选择同时受两个相反约束支配：

- **launch/派发地板项** `floor(N)`：随 N 增大而增大（每 block 的派发/回收成本）；实测同款芯片另一个算子
  blockDim 1→3.2 / 4→2.56 / 7→2.20 / 8→1.90 / 14→2.36 / 24→5.4us（X64）。本算子 no-op 探针在 40 block 下 4.0-5.2us。
- **per-core MTE 项** `share(N) / BW_core`：随 N 增大而减小；AIV 侧 **per-core MTE 吞吐约 80-110 GB/s**（L2 供数），
  `share = totalBytes / N`。

最优 N 是 `min_N max(floor(N), share(N)/BW_core)`，**不同流量档位落在不同的 N 上**，因此正确做法是 host 侧按总流量分档，
而不是全域统一核数：

```
totalBytes 小时（地板主导）：维持较小的核数（本例 40）
totalBytes 大时（per-core MTE 主导）：用满可用 AIV（本例 48）
阈值落在两者曲线的交点；本例的 case 集在 12.2MB 与 33.5MB 之间无样本，阈值在该区间内等价（取 16MB）
```

实现上核数用**运行期探测**取得而非硬编码（`aclrtGetSocName()` 判 910B2* → 48，未知 SoC 回退 40），
因为同一份二进制要跑在 20 AIC/40 AIV（910B3/B4）与 24 AIC/48 AIV（910B2C）两种形态上。

## 适用场景
- **算子类型**：纯 elementwise / broadcast（每元素独立、读写字节数固定），`AIV_ONLY` 任务类型
- **瓶颈类型**：同时存在「与 shape 无关的 launch/唤醒地板」和「per-core MTE 上限」两类约束时
- **前提条件**：
  1. host 能拿到 `totalBytes`（本例拍平成 1D 后 `numel * sizeof(dtype)`），且 tiling 分档是 host 侧可改的
  2. 核数可运行期探测（或按 SoC 分档），且 tile→核映射不依赖固定核数
  3. 必须逐档验证：**地板档（小流量）用大核数会回退**（本例 4MB 档 48 核 +15~24%，2 次复现）
- **预期收益**：本例 mid 档（33-90MB）单 case -13~-20%；全域 geomean +1.6%（对冻结基线）/ +2.9%（对同窗口基线等价体）

## 实现要点
- host：`usedCoreNum = (totalBytes <= TRAFFIC_GATE) ? CORE_SMALL : aivDetected`；
  `elemNum = ceil(total/blockElems)`、`tasksPerCore = ceil(elemNum/usedCoreNum)` 随核数重算；
  小流量档的 `blockElems` 分档**不要**同时放大（本例 UB-max 整块在 1M 档 +5%，见 f15）
- kernel：`Process()` 的循环边界（`tileEnd` / 是否尾块）**预计算**，去掉每 tile 的整数除与分支
  （节省的是每 tile 的标量延迟，不是吞吐）
- 与 dtype 分档正交：bf16 若已合并为单 fp32 scratch，UB 预算按 14B/elem 计，可吃到更大的 `blockElems`
- **门控纪律**：核数改动的 A/B 必须在**同一时间窗口**内做 40 核对照（本环境 case 级噪声 ±10~25%，
  跨窗口比较会把环境漂移误判为收益）

## 边界 / 实测否定项
- [negation] 全域统一小 blockDim（X64 的 8 核）应用到有真实搬移量的 elementwise：
  每核 MTE 饱和，本例 case0 +68% / case18 +81% / case2 +44%（见 f15）
- [negation] 全域统一大核数（48）：4MB 档 +15~24%（派发项变贵），必须分档
- [negation] 与「UB-max 整块 DataCopy 合并」叠加：1M 档 40 核 +5%（块/barrier 数量不是本类算子的杠杆）
- 本卡证据为 `single_op`；用前按上文的 `max(floor(N), share/BW_core)` 在两三个流量档位实测标定，不要直接搬用 48/16MB

## 来源
自动发现于 Exp 算子进化 round 2（node n6 = round_2/parallel_1）。变体全量 20 case geomean **5.0036x**（20/20 精度，
per-case `msprof --quick`、warm-up=2、device 3、持设备锁）；同窗口 40 核对照的基线等价体 4.8621x。
反向证据来自 round 1 的 n1（全域 48 AIV + 32B-chunk 细粒度连续区间 + 余数摊分 = 4.5402x，-6.6%）：
方向（多一点并行）没错，错在**粒度与作用域**。
