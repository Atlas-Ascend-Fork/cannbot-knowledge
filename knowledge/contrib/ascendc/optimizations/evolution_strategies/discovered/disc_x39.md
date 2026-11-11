---
type: Optimization
title: "X39: host 侧全写 workspace 免零初始化（at::zeros → at::empty）"
description: "算子 host 侧每次 forward 分配大块 workspace 或输出 buffer 时，若 kernel 会写满全部区域（无读前未写），可用 at::empty 替代 at::zeros，消除每次调用对数百 MB~GB 级内存的 memset。必须逐区域审计；存在 padded/未写行被后续读取时禁用。"
tags:
  - task.optimization
  - topic.data_movement
status: draft
sources:
  - resource: https://gitcode.com/cann/cannbot-knowledge/merge_requests/103
    role: primary
created_at: "2026-10-13T00:00:00Z"
updated_at: "2026-11-03T16:45:00Z"
platforms:
  - a2
---

# Strategy X39: host 侧全写 workspace 免零初始化（at::zeros → at::empty）

## 核心思路
算子 host 侧每次 forward 调用分配大块 workspace（及输出 buffer）时，若 kernel 会**写满全部区域**（无读前未写），用 `at::empty` 替代 `at::zeros`，消除每次调用对数百 MB~GB 级内存的 memset（清零写）。大 shape 下 memset 可能成为 memory-bound 地板，消除后直接降低每次调用的固定成本。

## 适用场景
- host 分配大 workspace / 输出 buffer，且 kernel 顺序写满所有区域（无读前未写）
- 大 shape 的 memory-bound 地板场景
- 与"动态核数"（blockDim = min(coreNum, totalTasks)）配合：小 shape 免拉满核、大 shape 免 memset

## 实现要点
1. 审查 workspace 各分区（如 wsK/wsV/wsS/wsP/wsO/wsMeta）是否全部被 kernel 写入后才被读——确认无读前未写
2. `at::zeros({totalBytes})` → `at::empty({totalBytes})`；输出 buffer 同理（只读实际写的行时安全）
3. 动态核数 `blockDim = min(coreNum, totalTasks)`，小任务不拉起空转核
4. 注意：**不能**对部分写/依赖零初始化的区域用 empty（会引入垃圾值 NaN/未定义行为）——必须逐区域审计

## 约束 / 红线
- 仅当 kernel 写满全部分配区域时安全；有 padded/未写行被后续读取时禁用
- 这是 host 侧分配优化，不改 kernel 计算逻辑；与 P54（launch 合并）互补但不同（P54 减 launch 次数，本策略减 memset 成本）

## 验证方法
- **同设备 A/B**：固定 shape 与输入，交替运行 zeros 与 empty 版本，取多次 warmup 后的中位数；确认 memset kernel 已从时间线消失且输出一致。
- **全量精度**：覆盖全部 shape、workspace 分区的空/满写入路径、padded 行与输出尾部；逐元素与参考实现比对，确认无 NaN/垃圾值。
- **容量审计**：逐区域核对 workspace（wsK/wsV/wsS/wsP/wsO/wsMeta）与输出 buffer 的写入覆盖范围，确认没有读前未写区域；动态核数下任务覆盖完整。
