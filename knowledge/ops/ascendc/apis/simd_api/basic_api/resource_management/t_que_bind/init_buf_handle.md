---
type: API
title: InitBufHandle
description: 为TQue、TBuf对象的内存块进行内存分配操作，包括设置内存块的大小和地址等。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.memory_management]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/resource_management/TQueBind/InitBufHandle.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---
# InitBufHandle

头文件路径为："basic_api/kernel_tpipe.h"。

为TQue、TBuf对象的内存块进行内存分配操作，包括设置内存块的大小，指向的地址等。

约束：-   TQue、TBuf类继承自TQueBind类，所以TQue、TBuf对象也可使用该接口。
-   目前只提供给自定义TBufPool初始化TQue、TBuf的内存块时使用。

仅 Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 200I/500 A2 推理产品、Atlas 推理系列产品AI Core、Atlas 训练系列产品 支持。

<!-- cannbot:related:start -->
## 相关

- [InitBuffer](../t_buf_pool/init_buffer.md)（`related`）：常规 TBufPool InitBuffer 直接为 TQue/TBuf 分配内存，而 InitBufHandle 是自定义池手工绑定路径，可据是否自主管理地址选择。
- [InitStartBufHandle](init_start_buf_handle.md)（`same_topic`）：InitStartBufHandle 与《InitBufHandle》的实质衔接是：InitStartBufHandle 与 InitBufHandle/GetBufHandle 围绕同一 TQueBind 缓冲句柄起点和获取流程。
<!-- cannbot:related:end -->
