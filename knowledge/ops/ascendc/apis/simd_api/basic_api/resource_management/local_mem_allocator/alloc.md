---
type: API
title: Alloc
description: 根据用户指定的逻辑位置、数据类型、数据长度返回对应的LocalTensor对象。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.memory_management]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/resource_management/LocalMemAllocator/Alloc.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---
# Alloc

头文件路径为："basic_api/kernel_tensor.h"。

根据用户指定的逻辑位置、数据类型、数据长度返回对应的LocalTensor对象。

约束：- 针对Ascend 950PR/Ascend 950DT，对UB的内存分配，会基于静态内存的基础上进行分配，即动态内存初始位置，参考内存层级。

- 当前暂不支持与L1 Buffer, L0A Buffer, L0B Buffer, L0C Buffer, BiasTable静态数组混用。

仅 Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 推理系列产品AI Core、Atlas 推理系列产品Vector Core 支持。

<!-- cannbot:related:start -->
## 相关

- [LocalMemAllocatorConstructor](local_mem_allocator_constructor.md)（`related`）：构造接口说明“LocalMemAllocator构造函数。”并建立唯一 allocator 对象；其消费接口“根据用户指定的逻辑位置、数据类型、数据长度返回对应的LocalTensor对象。”，说明构造完成后的核心分配动作和返回对象。
<!-- cannbot:related:end -->
