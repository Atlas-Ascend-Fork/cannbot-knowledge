---
type: API
title: Tiling下沉
description: Tiling下沉接口索引。
tags: [task.lookup, topic.programming_model]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/Tiling_sink/Tiling_sink.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# Tiling下沉

Tiling 下沉场景下，Tiling 函数从 Host 侧下沉到 AI CPU 执行，用于降低 Host 侧开销或支持图模式下的 Tiling 计算。本入口提供 DEVICE_IMPL_OP_OPTILING 宏的说明。
DEVICE_IMPL_OP_OPTILING 宏用于生成 Tiling 下沉的注册类，通过调用注册类的 Tiling 成员函数注册需要下沉的 Tiling 函数。Tiling 函数签名接受 gert::TilingContext* 输入，返回 ge::graphStatus。
使用时通过 DEVICE_IMPL_OP_OPTILING(optype).Tiling(func) 完成注册，optype 为算子类型。

<!-- cannbot:related:start -->
## 相关

- [开启Tiling下沉](../../../guides/programming_guide/advanced_programming/operator_graph_development/enable_tiling_sink.md)（`explains`）：该指南解释何时把 Host Tiling 下沉到 AI CPU、如何开启图模式流程，补足索引卡只有注册宏而缺少的使用决策和端到端步骤。
- [DEVICE_IMPL_OP_OPTILING](device_impl_op_optiling.md)（`same_topic`）：Tiling下沉卡正文唯一具体能力就是 DEVICE_IMPL_OP_OPTILING；目标卡给出该宏生成注册类及 Tiling(func) 注册函数的完整契约。
<!-- cannbot:related:end -->
