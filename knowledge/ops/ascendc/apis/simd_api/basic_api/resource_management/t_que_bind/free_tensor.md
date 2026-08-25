---
type: API
title: FreeTensor
description: 释放TQueBind队列中的指定Tensor。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.memory_management]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/resource_management/TQueBind/FreeTensor.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---
# FreeTensor

头文件路径为："basic_api/kernel_tpipe.h"。

释放Que中的指定Tensor。

仅 Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 200I/500 A2 推理产品、Atlas 推理系列产品AI Core、Atlas 训练系列产品 支持。

<!-- cannbot:related:start -->
## 相关

- [DeQue](de_que.md)（`related`）：DeQue 获得的 LocalTensor 在消费结束后必须通过 FreeTensor 归还队列内存，完成所有权生命周期。
- [AllocTensor](alloc_tensor.md)（`same_topic`）：《AllocTensor》处理“从Que中分配Tensor，Tensor所占大小为InitBuffer时设置的每块内存长度。”。《FreeTensor》提供“释放TQueBind队列中的指定Tensor。”，其具体合同或探针直接接入AllocTensor/FreeTensor 与 EnQue/DeQue 的队列所有权、初始化和耗尽故障。
- [HasIdleBuffer](has_idle_buffer.md)（`same_topic`）：HasIdleBuffer 与《FreeTensor》的实质衔接是：HasIdleBuffer 判断队列是否可分配，需结合 Alloc/Free、EnQue/DeQue 和队列状态解释。
<!-- cannbot:related:end -->
