---
type: API
title: SetVectorMask
description: 矢量计算时设置mask，支持Normal模式控制单次迭代参与计算元素和Counter模式控制总计算元素个数。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.masking]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/mask_operations/SetVectorMask.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# SetVectorMask

设置 Vector Mask，控制矢量计算接口中参与计算的元素。支持 Count 模式（按元素计数）和 Norm 模式（按比特位）。头文件 `basic_api/kernel_operator_vec_intf.h`。支持 950/a2/a3。
