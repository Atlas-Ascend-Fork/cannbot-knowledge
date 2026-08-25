---
type: API
title: GetCurAddr
description: 返回当前物理位置空闲的起始地址。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.memory_management]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/resource_management/LocalMemAllocator/GetCurAddr.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---
# GetCurAddr

头文件路径为："basic_api/kernel_tensor.h"。

返回当前物理位置空闲的起始地址。

仅 Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 推理系列产品AI Core、Atlas 推理系列产品Vector Core 支持。

<!-- cannbot:related:start -->
## 相关

- [GetBaseAddr](../t_pipe/get_base_addr.md)（`related`）：GetBaseAddr说明根据传入的logicPos（逻辑抽象位置）获取该位置的基础地址，只在CPU调试场景下生效。通常用于计算Tensor在logicPos的偏移地址。
- [LocalMemAllocatorConstructor](local_mem_allocator_constructor.md)（`related`）：构造后的起始地址以及每次 Alloc 后的下一空闲地址都可由 GetCurAddr 核验。
- [Alloc](alloc.md)（`same_topic`）：每次 Alloc 从当前空闲地址切分空间并推进游标，GetCurAddr 可在连续分配前核对下一地址。
- [GetCurAddr](../custom_t_buf_pool/get_cur_addr.md)（`same_topic`）：焦点处理自定义 TBufPool 当前地址游标的读取、设置与生命周期；GetCurAddr正文说明“返回当前物理位置空闲的起始地址”。候选读写同一个 pool 游标/块计数，或决定这些值何时初始化、复位和失效。
- [LocalMemAllocator简介](local_mem_allocator_intro.md)（`same_topic`）：GetCurAddr说明返回当前物理位置空闲的起始地址。
- [SetCurAddr](../custom_t_buf_pool/set_cur_addr.md)（`same_topic`）：SetCurAddr说明设置自定义TBufPool已分配完的地址，保证后续内存块从指定地址开始分配。
<!-- cannbot:related:end -->
