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

- [GetCurAddr](get_cur_addr.md)（`related`）：SetCurAddr“设置自定义TBufPool已经被分配完的地址”；GetCurAddr“获取当前已经被自定义TBufPool分配的地址，用户可以从该地址值开始向后分配内存块。”。两者管理同一自定义池的分配游标。
<!-- cannbot:related:end -->
