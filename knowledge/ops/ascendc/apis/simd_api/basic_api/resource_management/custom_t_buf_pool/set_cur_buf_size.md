---
type: API
title: SetCurBufSize
description: 设置自定义TBufPool当前已分配的内存块个数。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.memory_management]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/resource_management/custom_TBufPool/SetCurBufSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---
# SetCurBufSize

头文件路径为："basic_api/kernel_tpipe.h"。

设置当前已经被自定义TBufPool分配的内存块个数。

仅 Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 推理系列产品AI Core、Atlas 训练系列产品、Kirin X90、Kirin 9030 支持。

<!-- cannbot:related:start -->
## 相关

- [Init](init.md)（`related`）：SetCurBufSize说明设置自定义TBufPool当前已分配的内存块个数。
- [GetCurAddr](get_cur_addr.md)（`same_topic`）：焦点处理自定义 TBufPool 当前地址游标的读取、设置与生命周期；SetCurBufSize正文说明“设置自定义TBufPool当前已分配的内存块个数”。候选读写同一个 pool 游标/块计数，或决定这些值何时初始化、复位和失效。
- [GetCurBufSize](get_cur_buf_size.md)（`same_topic`）：GetCurBufSize 读取已分配块数，SetCurBufSize 更新同一计数，是自定义分配器状态的读写对。
<!-- cannbot:related:end -->
