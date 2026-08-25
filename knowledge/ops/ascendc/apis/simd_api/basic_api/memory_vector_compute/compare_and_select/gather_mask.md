---
type: API
title: GatherMask
description: 以内置固定模式或用户自定义Tensor为gather mask，从源操作数中选取元素写入目的操作数。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.compute.elementwise.comparison_logic]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/compare_and_select/GatherMask.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# GatherMask

根据 mask 从源 tensor 中收集有效元素到目的 tensor。头文件 `basic_api/kernel_operator_vec_cmpsel_intf.h`。支持 950/a2/a3。

<!-- cannbot:related:start -->
## 相关

- [Compare](compare.md)（`related`）：《Compare》明确“逐元素比较两个tensor大小，结果为真的对应比特位为1，否则为0，支持LT、GT、GE、EQ、NE、LE六种比较模式。”；它与《GatherMask》的“以内置固定模式或用户自定义Tensor为gather mask，从源操作数中选取元素写入目的操作数。”在实际调用参数、数据流或结果校验上直接衔接。
- [AscReduce](../../../c_api/vector_compute/asc_reduce.md)（`same_topic`）：《AscReduce》说明以内置固定模式对应的二进制或者用户自定义输入的数值对应的gather mask（数据收集的掩码），从源操作数中选取元素写入目的操作数中。；《GatherMask》说明以内置固定模式或用户自定义Tensor为gather mask，从源操作数中选取元素写入目的操作数。。二者在AscReduce是按mask压缩选中元素的gather语义，GatherMask提供等价数据选择，AscGetRsvdCount读取实际保留数量上存在可执行的直接衔接。
<!-- cannbot:related:end -->
