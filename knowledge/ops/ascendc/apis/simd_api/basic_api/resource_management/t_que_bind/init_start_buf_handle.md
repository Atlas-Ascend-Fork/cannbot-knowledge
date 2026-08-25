---
type: API
title: InitStartBufHandle
description: 设置TQue/TBuf的起始内存块指针、内存块个数和每块内存块的大小。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.memory_management]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/resource_management/TQueBind/InitStartBufHandle.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---
# InitStartBufHandle

头文件路径为："basic_api/kernel_tpipe.h"。

设置TQue/TBuf的起始内存块指针、内存块的个数、每一块内存块的大小。

约束：-   TQue、TBuf类继承自TQueBind类，所以TQue、TBuf对象也可使用该接口。

-   该接口目前只提供给自定义TBufPool初始化TQue、TBuf的内存块时使用。
-   当使用TBuf对象调用该接口时，入参num必须为1。

仅 Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 200I/500 A2 推理产品、Atlas 推理系列产品AI Core、Atlas 训练系列产品 支持。

<!-- cannbot:related:start -->
## 相关

- [GetBufHandle](../custom_t_buf_pool/get_buf_handle.md)（`same_topic`）：InitStartBufHandle 与《GetBufHandle》的实质衔接是：InitStartBufHandle 与 InitBufHandle/GetBufHandle 围绕同一 TQueBind 缓冲句柄起点和获取流程。
- [InitBufHandle](init_buf_handle.md)（`same_topic`）：InitStartBufHandle 与《InitBufHandle》的实质衔接是：InitStartBufHandle 与 InitBufHandle/GetBufHandle 围绕同一 TQueBind 缓冲句柄起点和获取流程。
<!-- cannbot:related:end -->
