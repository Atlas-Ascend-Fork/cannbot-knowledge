---
type: Guide
title: 运行验证时AllocTensor/FreeTensor失败
description: 通过NPU进行核函数的运行验证时，出现挂死现象；通过CPU进行核函数的运行验证时，出现AllocTensor/FreeTensor失败的报错，日志报错和调用栈打印如下：
tags: [task.lookup, topic.implementation]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/programming_guide/appendix/faq/alloc_free_tensor_failure.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# 运行验证时AllocTensor/FreeTensor失败

## 现象描述
通过NPU进行核函数的运行验证时，出现挂死现象；通过CPU进行核函数的运行验证时，出现AllocTensor/FreeTensor失败的报错，日志报错和调用栈打印如下：
## 问题根因
根据日志信息“current size is 4,  max buffer number in same queue position  is 4”可以明确该问题是因为同一个TPosition上QUE Buffer的数量超出限制导致。
同一个TPosition上的所有Queue，连续调用AllocTensor接口申请的Tensor数量，根据AI处理器型号的不同，有数量约束。申请Buffer时，需要满足该约束。
Atlas 训练系列产品不超过4个。
Atlas 推理系列产品AI Core不超过8个。
Atlas 推理系列产品Vector Core不超过8个。
Atlas A2 训练系列产品/Atlas A2 推理系列产品不超过8个。
Atlas A3 训练系列产品/Atlas A3 推理系列产品不超过8个。
Atlas 200I/500 A2 推理产品不超过8个。
不满足该约束，在后续使用AllocTensor/FreeTensor可能会出现分配资源失败。比如：
## 处理步骤
如果确实有多块buffer使用，可以将多个buffer合并到一块buffer，通过偏移使用。样例如下：

<!-- cannbot:related:start -->
## 相关

- [FreeTensor](../../../../apis/simd_api/basic_api/resource_management/t_que/free_tensor.md)（`explains`）：释放Que中的指定Tensor。；不满足该约束，在后续使用AllocTensor/FreeTensor可能会出现分配资源失败。；FAQ 提供同一 API 在队列 buffer 数量超限时的故障信号与处置。
- [TQue 输入未释放导致循环 AllocTensor 卡死](../../../../runbooks/compilation/tque_dequeue_must_end_with_freetensor.md)（`related`）：通过NPU进行核函数的运行验证时，出现挂死现象；通过CPU进行核函数的运行验证时，出现AllocTensor/FreeTensor失败的报错，日志报错和调用栈打印如下：；`DeQue` 只把已入队 Tensor 交给消费者，不等于把底层 buffer 归还给队列；循环在消费完成后遗漏 `FreeTensor`，有限 depth 的输入 buffer 被逐轮占用，后续 `AllocTensor` 无空闲 buffer 可分配而无进展。。候选为焦点同类挂死信号提供另一项必须排查的逐轮 buffer 泄漏机制。
<!-- cannbot:related:end -->
