---
type: API
title: HasIdleBuffer
description: 查询Que中是否有空闲的内存块可供AllocTensor分配，不支持Tensor原地操作场景。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.memory_management]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/resource_management/TQue/HasIdleBuffer.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---
# HasIdleBuffer

头文件路径为："basic_api/kernel_tpipe.h"。

查询Que中是否有空闲的内存块。

约束：该接口不支持Tensor原地操作，即TQue的depth设置为0的场景。

仅 Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 200I/500 A2 推理产品、Atlas 推理系列产品AI Core、Atlas 训练系列产品、Kirin X90、Kirin 9030 支持。

<!-- cannbot:related:start -->
## 相关

- [AllocTensor](alloc_tensor.md)（`related`）：查询Que中是否有空闲的内存块；从Que中分配Tensor，Tensor所占大小为InitBuffer时设置的每块内存长度。前者用于在执行后者前检查可分配块，二者构成 TQue 的容量探测与分配操作链。
<!-- cannbot:related:end -->
