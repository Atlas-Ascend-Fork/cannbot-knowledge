---
type: API
title: DeQue
description: 将Tensor从队列中取出用于后续处理，支持non-inplace和inplace两种接口，可通过TQueBind指定源和目的位置。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.memory_management]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/resource_management/TQue/DeQue.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---
# DeQue

头文件路径为："basic_api/kernel_tpipe.h"。

将Tensor从队列中取出，用于后续处理。

约束：-   对空队列执行DeQue是一种异常行为，会在CPU调测时报错。
-   non-inplace接口和指定源和目的位置的接口，需要将TQueBind的depth模板参数设置为非零值；inplace接口，需要将TQueBind的depth模板参数设置为0。

仅 Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 200I/500 A2 推理产品、Atlas 推理系列产品AI Core、Atlas 训练系列产品、Kirin X90、Kirin 9030 支持。

<!-- cannbot:related:start -->
## 相关

- [AllocTensor](alloc_tensor.md)（`related`）：从Que中分配Tensor，Tensor所占大小为InitBuffer时设置的每块内存长度。；将Tensor从队列中取出，用于后续处理。；分配并入队的缓冲最终由消费者 DeQue 取出，二者处在同一有限队列生命周期。
- [EnQue](en_que.md)（`related`）：将Tensor从队列中取出，用于后续处理；将Tensor push到队列。EnQue 提交生产完成的 LocalTensor，DeQue 在后续阶段取出同一队列元素；两端定义流水线中必须成对使用的生产者—消费者队列操作。
<!-- cannbot:related:end -->
