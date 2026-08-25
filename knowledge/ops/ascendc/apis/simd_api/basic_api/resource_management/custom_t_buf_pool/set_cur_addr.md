---
type: API
title: SetCurAddr
description: 设置自定义TBufPool已分配完的地址，保证后续内存块从指定地址开始分配。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.memory_management]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/resource_management/custom_TBufPool/SetCurAddr.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---
# SetCurAddr

头文件路径为："basic_api/kernel_tpipe.h"。

设置自定义TBufPool已经被分配完的地址，比如初始化时一共申请了32k的内存大小，给某一个TQue分配了8K，则需要调用该接口以保证后续的内存块从8K开始分配。

仅 Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 推理系列产品AI Core、Atlas 训练系列产品、Kirin X90、Kirin 9030 支持。

<!-- cannbot:related:start -->
## 相关

- [ExternImplBufpool](extern_impl_bufpool.md)（`related`）：不连续内存块或跨 TQue 共享时需显式更新当前地址，正是 ExternImplBufpool 允许自定义的核心能力。
- [GetCurBufSize](get_cur_buf_size.md)（`related`）：地址游标需与已分配块数共同更新，否则池状态会出现重叠或漏记。
- [GetCurAddr](get_cur_addr.md)（`same_topic`）：焦点处理自定义 TBufPool 当前地址游标的读取、设置与生命周期；SetCurAddr正文说明“设置自定义TBufPool已分配完的地址，保证后续内存块从指定地址开始分配”。候选读写同一个 pool 游标/块计数，或决定这些值何时初始化、复位和失效。
- [GetCurAddr](../local_mem_allocator/get_cur_addr.md)（`same_topic`）：SetCurAddr说明设置自定义TBufPool已分配完的地址，保证后续内存块从指定地址开始分配。
<!-- cannbot:related:end -->
