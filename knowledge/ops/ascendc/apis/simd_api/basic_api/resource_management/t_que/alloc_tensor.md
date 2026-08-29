---
type: API
title: AllocTensor
description: 从Que中分配Tensor，Tensor大小为InitBuffer时设置的每块内存长度，支持non-inplace和inplace两种接口。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.memory_management]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/resource_management/TQue/AllocTensor.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---
# AllocTensor

头文件路径为："basic_api/kernel_tpipe.h"。

从Que中分配Tensor，Tensor所占大小为InitBuffer时设置的每块内存长度。

约束：-   同一个TPosition上的所有Queue，连续调用AllocTensor接口申请的Tensor数量，根据AI处理器型号的不同，有数量约束。申请Buffer时，需要满足该约束。

    - Ascend 950PR/Ascend 950DT不超过8个。

    - Atlas A3 训练系列产品/Atlas A3 推理系列产品不超过8个。

    - Atlas A2 训练系列产品/Atlas A2 推理系列产品不超过8个。

    - Atlas 200I/500 A2 推理产品不超过8个。

    - Atlas 推理系列产品AI Core不超过8个。

    - Atlas 推理系列产品Vector Core不超过8个。

仅 Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 200I/500 A2 推理产品、Atlas 推理系列产品AI Core、Atlas 训练系列产品、Kirin X90、Kirin 9030 支持。

<!-- cannbot:related:start -->
## 相关

- [TQue 输入未释放导致循环 AllocTensor 卡死](../../../../../runbooks/compilation/tque_dequeue_must_end_with_freetensor.md)（`exemplifies`）：同一个TPosition上的所有Queue，连续调用AllocTensor接口申请的Tensor数量，根据AI处理器型号的不同，有数量约束。；`DeQue` 只把已入队 Tensor 交给消费者，不等于把底层 buffer 归还给队列；有限申请数与未归还缓冲共同解释循环中后续 AllocTensor 无进展的失败签名。
- [DeQue](de_que.md)（`related`）：从Que中分配Tensor，Tensor所占大小为InitBuffer时设置的每块内存长度。；将Tensor从队列中取出，用于后续处理。；分配并入队的缓冲最终由消费者 DeQue 取出，二者处在同一有限队列生命周期。
- [EnQue](en_que.md)（`related`）：从Que中分配Tensor，Tensor所占大小为InitBuffer时设置的每块内存长度。；将Tensor push到队列。；AllocTensor 取得生产缓冲后由 EnQue 提交给队列，构成生产侧所有权流转。
- [FreeTensor](free_tensor.md)（`related`）：从Que中分配Tensor，Tensor所占大小为InitBuffer时设置的每块内存长度。；释放Que中的指定Tensor。；AllocTensor 占用的有限缓冲必须由 FreeTensor 归还，形成资源闭环。
- [HasIdleBuffer](has_idle_buffer.md)（`related`）：查询Que中是否有空闲的内存块；从Que中分配Tensor，Tensor所占大小为InitBuffer时设置的每块内存长度。前者用于在执行后者前检查可分配块，二者构成 TQue 的容量探测与分配操作链。
<!-- cannbot:related:end -->
