---
type: API
title: InitBuffer
description: 用于为TQue等队列和TBuf分配内存。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.memory_management]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/resource_management/TPipe/InitBuffer.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---
# InitBuffer

头文件路径为："basic_api/kernel_tpipe.h"。

用于为TQue等队列和TBuf分配内存。

约束：-   InitBuffer申请的内存会在TPipe对象销毁时通过析构函数自动释放，无需手动释放。
-   如果需要重新分配InitBuffer申请的内存，可以调用Reset，再调用InitBuffer接口。
-   一个kernel中所有使用的Buffer数量之和不能超过64。
-   自定义地址InitBuffer方式分配不建议与不指定地址的混用，可能会导致内存冲突。

- 针对Ascend 950PR/Ascend 950DT，对UB的内存分配，会基于静态内存的基础上进行分配，即动态内存初始位置，参考内存层级。

- 当前暂不支持与L1 Buffer, L0A Buffer, L0B Buffer, L0C Buffer, BiasTable静态数组混用。

仅 Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 200I/500 A2 推理产品、Atlas 推理系列产品AI Core、Atlas 训练系列产品、Kirin X90、Kirin 9030 支持。

<!-- cannbot:related:start -->
## 相关

- [TBuf 三参数 InitBuffer 触发 isTQue 静态断言](../../../../../runbooks/compilation/tbuf_initbuffer_uses_two_arguments.md)（`exemplifies`）：保留 `TQue` 的 `(queue, depth, bytes)` 三参数调用；仅对 `TBuf` 删除队列深度参数，改用 `(buffer, bytes)` 两参数调用。；用于为TQue等队列和TBuf分配内存。runbook 是 TPipe InitBuffer 面向两类对象时重载合同被误用的具体实例。
<!-- cannbot:related:end -->
