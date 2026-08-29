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
