---
type: API
title: GetCurBufSize
description: 获取自定义TBufPool当前已分配的内存块个数。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.memory_management]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/resource_management/custom_TBufPool/GetCurBufSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---
# GetCurBufSize

头文件路径为："basic_api/kernel_tpipe.h"。

获取当前已经被自定义TBufPool分配的内存块个数。

仅 Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 推理系列产品AI Core、Atlas 训练系列产品、Kirin X90、Kirin 9030 支持。

<!-- cannbot:related:start -->
## 相关

- [ExternImplBufpool](extern_impl_bufpool.md)（`related`）：自定义分配实现需要读取当前剩余/可用区大小，避免跨越池边界。
- [GetCurAddr](get_cur_addr.md)（`related`）：块数与当前地址共同描述自定义池分配游标，诊断重叠或越界需同时检查。
- [SetCurAddr](set_cur_addr.md)（`related`）：地址游标需与已分配块数共同更新，否则池状态会出现重叠或漏记。
- [SetCurBufSize](set_cur_buf_size.md)（`same_topic`）：GetCurBufSize 读取已分配块数，SetCurBufSize 更新同一计数，是自定义分配器状态的读写对。
<!-- cannbot:related:end -->
