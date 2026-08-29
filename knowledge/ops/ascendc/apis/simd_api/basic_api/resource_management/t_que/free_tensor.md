---
type: API
title: FreeTensor
description: 释放Que中的指定Tensor，需与AllocTensor配对使用。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.memory_management]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/resource_management/TQue/FreeTensor.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---
# FreeTensor

头文件路径为："basic_api/kernel_tpipe.h"。

释放Que中的指定Tensor。

仅 Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 200I/500 A2 推理产品、Atlas 推理系列产品AI Core、Atlas 训练系列产品、Kirin X90、Kirin 9030 支持。

<!-- cannbot:related:start -->
## 相关

- [FreeTensor早释使队列别名被下一轮DMA覆盖](../../../../../runbooks/precision/reinterpret_tensor_alias_must_outlive_queue_release.md)（`exemplifies`）：`FreeTensor` 把该队列槽标为可复用，不表示所有持有它的视图已经完成消费。下一子 tile 的 `AllocTensor + DataCopyPad` 可以用 MTE2 覆盖同一 UB，而前一 tile 的 V 流水仍在读取，于是产生真正的数据竞争：有时读到 NaN，有时读到错误有限值，表现随运行时序变化。；释放Que中的指定Tensor。；目标是触发队列槽复用的接口，焦点进一步给出别名仍被异步消费时过早释放的竞态机制。
- [TQue 输入未释放导致循环 AllocTensor 卡死](../../../../../runbooks/compilation/tque_dequeue_must_end_with_freetensor.md)（`exemplifies`）：Runbook 说明“`DeQue` 只把已入队 Tensor 交给消费者，不等于把底层 buffer 归还给队列”；FreeTensor API执行“释放Que中的指定Tensor。”。该动作正是修复循环中输入 buffer 不归还导致的队列耗尽。
- [运行验证时AllocTensor/FreeTensor失败](../../../../../guides/programming_guide/appendix/faq/alloc_free_tensor_failure.md)（`explains`）：释放Que中的指定Tensor。；不满足该约束，在后续使用AllocTensor/FreeTensor可能会出现分配资源失败。；FAQ 提供同一 API 在队列 buffer 数量超限时的故障信号与处置。
- [AllocTensor](alloc_tensor.md)（`related`）：从Que中分配Tensor，Tensor所占大小为InitBuffer时设置的每块内存长度。；释放Que中的指定Tensor。；AllocTensor 占用的有限缓冲必须由 FreeTensor 归还，形成资源闭环。
<!-- cannbot:related:end -->
