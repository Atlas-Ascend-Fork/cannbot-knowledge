---
type: API
title: Warp函数
description: Warp函数索引，包含Vote、Shfl、Reduce与Lane ID类函数。
tags: [task.lookup, topic.programming_model.cooperative_groups]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/Warp_functions/Warp_functions.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# Warp函数

Warp 级别协同操作函数的总入口，包含 Warp Vote（投票表决）、Warp Shfl（数据交换）、Warp Reduce（归约）和 Lane ID（通道标识）四类函数。这些函数以 Warp（通常 32 个 Lane）为最小协同单位，支持 Warp 内的并行数据交换、条件聚合和归约运算。

<!-- cannbot:related:start -->
## 相关

- [同一Warp内避免分支跳转](../../../guides/operator_practice/simt_operator_optimization/control_flow/avoid_warp_branch.md)（`explains`）：Warp函数 与《同一Warp内避免分支跳转》的实质衔接是：Warp API 与 Warp 分支优化围绕同一 32-lane 执行和分歧成本，overview 提供成员之间的组合方式。
- [Warp Shfl类函数](warp_shfl_functions/warp_shfl_functions.md)（`same_topic`）：Warp Shfl类函数 与《Warp函数》的实质衔接是：Warp Shfl 总览覆盖 general/down/up/xor 四种 lane 交换；coalesced/tile 对应入口和分支优化指南说明作用域及真实使用。
- [Warp函数](warp_functions_intro.md)（`same_topic`）：Warp函数 与《Warp函数》的实质衔接是：Warp API 与 Warp 分支优化围绕同一 32-lane 执行和分歧成本，overview 提供成员之间的组合方式。
<!-- cannbot:related:end -->
