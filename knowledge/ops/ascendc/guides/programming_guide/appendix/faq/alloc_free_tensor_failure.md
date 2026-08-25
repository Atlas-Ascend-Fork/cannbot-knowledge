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

- [AllocTensor](../../../../apis/simd_api/basic_api/resource_management/t_que/alloc_tensor.md)（`explains`）：《运行验证时AllocTensor/FreeTensor失败》给出“通过NPU进行核函数的运行验证时，出现挂死现象；通过CPU进行核函数的运行验证时，出现AllocTensor/FreeTensor失败的报错，日志报错和调用栈打印如下：”；该约束/探针可直接复现、解释或前置验证《AllocTensor》中的“从Que中分配Tensor，Tensor大小为InitBuffer时设置的每块内存长度，支持non-inplace和inplace两种接口。”。
- [AllocTensor](../../../../apis/simd_api/basic_api/resource_management/t_que_bind/alloc_tensor.md)（`explains`）：《AllocTensor》处理“从Que中分配Tensor，Tensor所占大小为InitBuffer时设置的每块内存长度。”。《运行验证时AllocTensor/FreeTensor失败》提供“通过NPU进行核函数的运行验证时，出现挂死现象；通过CPU进行核函数的运行验证时，出现AllocTensor/FreeTensor失败的报错，日志报错和调用栈打印如下：”，其具体合同或探针直接接入AllocTensor/FreeTensor 与 EnQue/DeQue 的队列所有权、初始化和耗尽故障。
- [FreeTensor](../../../../apis/simd_api/basic_api/resource_management/t_que/free_tensor.md)（`explains`）：运行验证时AllocTensor/FreeTensor失败 的核心契约是“通过NPU进行核函数的运行验证时，出现挂死现象；通过CPU进行核函数的运行验证时，出现AllocTensor/FreeTensor失败的报错，日志报错和调用栈打印如下：”；FreeTensor 补充“释放Que中的指定Tensor，需与AllocTensor配对使用”。
- [TSCM](../../../../apis/simd_api/basic_api/resource_management/tscm/tscm.md)（`explains`）：TSCM 与《运行验证时AllocTensor/FreeTensor失败》的实质衔接是：TSCM 的 Queue/Buffer 生命周期需要成对 Alloc/Free、EnQue/DeQue 与所有权交接；所选故障卡分别覆盖空取、早释、重取和跨流水复用。
- [ACL 507035 — 空 TQue DeQue 触发 B16 路径异常](../../../../runbooks/compilation/tque_dequeue_requires_prior_enqueue_507035.md)（`related`）：ACL 507035 — 空 TQue DeQue 触发 B16 路径异常 与《运行验证时AllocTensor/FreeTensor失败》的实质衔接是：空队列 DeQue 违反 AllocTensor→EnQue→DeQue→FreeTensor 的所有权链；相关失败卡覆盖重复 DeQue、早释、未释放、InitBuffer 参数和验证报错，Sin/Cos 是该 B16 分支中实际触发计算。
- [TPipe和TQue编程范式](../../programming_model/ai_core_simd_programming/tpipe_tque_programming/tpipe_tque_paradigm.md)（`related`）：《TPipe和TQue编程范式》说明上一章阐述了TPipe‑TQue编程模型的底层设计原理：基于经典C/C++队列管道（Queue Pipeline）思想，将算子任务拆分为多级流水Stage，依靠TQue队列解决写后读数据依赖、依靠AllocTensor/FreeTensor解决读后写内存复用冲突，通过底层同步指令实现多单元异步并行的时序安全。；《运行验证时AllocTensor/FreeTensor失败》说明通过NPU进行核函数的运行验证时，出现挂死现象；通过CPU进行核函数的运行验证时，出现AllocTensor/FreeTensor失败的报错，日志报错和调用栈打印如下：。二者在TPipe/TQue范式用InitBuffer和Alloc/EnQue/DeQue/FreeTensor表达内存所有权与Stage同步，相关FAQ和故障直接验证生命周期约束上存在可执行的直接衔接。
- [TQue tensor 所有权只能 DeQue 一次](../../../../runbooks/compilation/tque_tensor_ownership_single_dequeue.md)（`related`）：TQue tensor 所有权只能 DeQue 一次 与《运行验证时AllocTensor/FreeTensor失败》的实质衔接是：TQue 元素必须严格 Alloc→EnQue→DeQue→Free 且只由一个消费者出队；相关 API、生命周期指南和失败卡覆盖临时值、早释、空队列及跨函数交接。
- [TQue 输入未释放导致循环 AllocTensor 卡死](../../../../runbooks/compilation/tque_dequeue_must_end_with_freetensor.md)（`related`）：FAQ 给出 Alloc/Free 失败与挂死的观测日志，可用于确认是否为 buffer 未归还而非计算耗时。
<!-- cannbot:related:end -->
