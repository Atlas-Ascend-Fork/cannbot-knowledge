---
type: API
title: AllocTensor
description: 从Que中分配Tensor，Tensor所占大小为InitBuffer时设置的每块内存长度。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.memory_management]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/resource_management/TQueBind/AllocTensor.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---
# AllocTensor

头文件路径为："basic_api/kernel_tpipe.h"。

从Que中分配Tensor，Tensor所占大小为InitBuffer时设置的每块内存长度。

约束：-   non-inplace接口分配的Tensor内容可能包含随机值。
-   non-inplace接口，需要将TQueBind的depth模板参数设置为非零值；inplace接口，需要将TQueBind的depth模板参数设置为0。

仅 Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 200I/500 A2 推理产品、Atlas 推理系列产品AI Core、Atlas 训练系列产品 支持。

<!-- cannbot:related:start -->
## 相关

- [ACL 507035 — 空 TQue DeQue 触发 B16 路径异常](../../../../../runbooks/compilation/tque_dequeue_requires_prior_enqueue_507035.md)（`exemplifies`）：《AllocTensor》处理“从Que中分配Tensor，Tensor所占大小为InitBuffer时设置的每块内存长度。”。《ACL 507035 — 空 TQue DeQue 触发 B16 路径异常》提供“B16 分支只入队原始 cos/sin，却从未入队的 fp32 队列 DeQue 作为 scratch；按 dtype 区分 DeQue 与 AllocTensor 后消除大规模路径 507035。”，其具体合同或探针直接接入AllocTensor/FreeTensor 与 EnQue/DeQue 的队列所有权、初始化和耗尽故障。
- [FreeTensor早释使队列别名被下一轮DMA覆盖](../../../../../runbooks/precision/reinterpret_tensor_alias_must_outlive_queue_release.md)（`exemplifies`）：《AllocTensor》处理“从Que中分配Tensor，Tensor所占大小为InitBuffer时设置的每块内存长度。”。《FreeTensor早释使队列别名被下一轮DMA覆盖》提供“fp32路径让计算张量别名队列张量时，compute完成前FreeTensor会触发UB复用，造成非确定性NaN和有限值错误。”，其具体合同或探针直接接入AllocTensor/FreeTensor 与 EnQue/DeQue 的队列所有权、初始化和耗尽故障。
- [TQue InitBuffer 须传深度和 uint32 长度](../../../../../runbooks/compilation/tque_initbuffer_requires_depth_and_uint32_length.md)（`exemplifies`）：《AllocTensor》处理“从Que中分配Tensor，Tensor所占大小为InitBuffer时设置的每块内存长度。”。《TQue InitBuffer 须传深度和 uint32 长度》提供“将 TBuf 的两参数 InitBuffer 写法套到 TQue 会无匹配重载；按 queue、bufferNum、uint32 len 三参数初始化后恢复构建。”，其具体合同或探针直接接入AllocTensor/FreeTensor 与 EnQue/DeQue 的队列所有权、初始化和耗尽故障。
- [TQue tensor 所有权只能 DeQue 一次](../../../../../runbooks/compilation/tque_tensor_ownership_single_dequeue.md)（`exemplifies`）：《AllocTensor》处理“从Que中分配Tensor，Tensor所占大小为InitBuffer时设置的每块内存长度。”。《TQue tensor 所有权只能 DeQue 一次》提供“FreeTensor 需要可写 LocalTensor lvalue，且同一队列元素只能 DeQue 一次；把队列所有权集中在明确的生产消费函数中可消除编译错误和重复出队。”，其具体合同或探针直接接入AllocTensor/FreeTensor 与 EnQue/DeQue 的队列所有权、初始化和耗尽故障。
- [TQue 输入未释放导致循环 AllocTensor 卡死](../../../../../runbooks/compilation/tque_dequeue_must_end_with_freetensor.md)（`exemplifies`）：《AllocTensor》处理“从Que中分配Tensor，Tensor所占大小为InitBuffer时设置的每块内存长度。”。《TQue 输入未释放导致循环 AllocTensor 卡死》提供“循环内 DeQue 的输入 Tensor 未归还 TQue，耗尽队列 buffer 后后续 AllocTensor 无进展；消费完成立即 FreeTensor。”，其具体合同或探针直接接入AllocTensor/FreeTensor 与 EnQue/DeQue 的队列所有权、初始化和耗尽故障。
- [运行验证时AllocTensor/FreeTensor失败](../../../../../guides/programming_guide/appendix/faq/alloc_free_tensor_failure.md)（`explains`）：《AllocTensor》处理“从Que中分配Tensor，Tensor所占大小为InitBuffer时设置的每块内存长度。”。《运行验证时AllocTensor/FreeTensor失败》提供“通过NPU进行核函数的运行验证时，出现挂死现象；通过CPU进行核函数的运行验证时，出现AllocTensor/FreeTensor失败的报错，日志报错和调用栈打印如下：”，其具体合同或探针直接接入AllocTensor/FreeTensor 与 EnQue/DeQue 的队列所有权、初始化和耗尽故障。
- [InitBuffer](../t_buf_pool/init_buffer.md)（`related`）：《AllocTensor》处理“从Que中分配Tensor，Tensor所占大小为InitBuffer时设置的每块内存长度。”。《InitBuffer》提供“为TQue或TBuf进行内存分配，支持指定内存块个数和大小。”，其具体合同或探针直接接入AllocTensor/FreeTensor 与 EnQue/DeQue 的队列所有权、初始化和耗尽故障。
- [InitBuffer](../t_pipe/init_buffer.md)（`related`）：《AllocTensor》处理“从Que中分配Tensor，Tensor所占大小为InitBuffer时设置的每块内存长度。”。《InitBuffer》提供“用于为TQue等队列和TBuf分配内存。”，其具体合同或探针直接接入AllocTensor/FreeTensor 与 EnQue/DeQue 的队列所有权、初始化和耗尽故障。
- [AllocTensor](../t_que/alloc_tensor.md)（`same_topic`）：《AllocTensor》处理“从Que中分配Tensor，Tensor所占大小为InitBuffer时设置的每块内存长度。”。《AllocTensor》提供“从Que中分配Tensor，Tensor大小为InitBuffer时设置的每块内存长度，支持non-inplace和inplace两种接口。”，其具体合同或探针直接接入AllocTensor/FreeTensor 与 EnQue/DeQue 的队列所有权、初始化和耗尽故障。
- [DeQue](../t_que/de_que.md)（`same_topic`）：《AllocTensor》处理“从Que中分配Tensor，Tensor所占大小为InitBuffer时设置的每块内存长度。”。《DeQue》提供“将Tensor从队列中取出用于后续处理，支持non-inplace和inplace两种接口，可通过TQueBind指定源和目的位置。”，其具体合同或探针直接接入AllocTensor/FreeTensor 与 EnQue/DeQue 的队列所有权、初始化和耗尽故障。
- [DeQue](de_que.md)（`same_topic`）：《AllocTensor》处理“从Que中分配Tensor，Tensor所占大小为InitBuffer时设置的每块内存长度。”。《DeQue》提供“将Tensor从队列中取出，用于后续处理。”，其具体合同或探针直接接入AllocTensor/FreeTensor 与 EnQue/DeQue 的队列所有权、初始化和耗尽故障。
- [EnQue](../t_que/en_que.md)（`same_topic`）：《AllocTensor》处理“从Que中分配Tensor，Tensor所占大小为InitBuffer时设置的每块内存长度。”。《EnQue》提供“将Tensor加入队列，返回是否入队成功，可通过TQueBind指定源和目的位置实现内存复用。”，其具体合同或探针直接接入AllocTensor/FreeTensor 与 EnQue/DeQue 的队列所有权、初始化和耗尽故障。
- [EnQue](en_que.md)（`same_topic`）：《AllocTensor》处理“从Que中分配Tensor，Tensor所占大小为InitBuffer时设置的每块内存长度。”。《EnQue》提供“将Tensor加入队列。”，其具体合同或探针直接接入AllocTensor/FreeTensor 与 EnQue/DeQue 的队列所有权、初始化和耗尽故障。
- [FreeTensor](../t_que/free_tensor.md)（`same_topic`）：《AllocTensor》处理“从Que中分配Tensor，Tensor所占大小为InitBuffer时设置的每块内存长度。”。《FreeTensor》提供“释放Que中的指定Tensor，需与AllocTensor配对使用。”，其具体合同或探针直接接入AllocTensor/FreeTensor 与 EnQue/DeQue 的队列所有权、初始化和耗尽故障。
- [FreeTensor](free_tensor.md)（`same_topic`）：《AllocTensor》处理“从Que中分配Tensor，Tensor所占大小为InitBuffer时设置的每块内存长度。”。《FreeTensor》提供“释放TQueBind队列中的指定Tensor。”，其具体合同或探针直接接入AllocTensor/FreeTensor 与 EnQue/DeQue 的队列所有权、初始化和耗尽故障。
- [HasIdleBuffer](has_idle_buffer.md)（`same_topic`）：HasIdleBuffer 与《AllocTensor》的实质衔接是：HasIdleBuffer 判断队列是否可分配，需结合 Alloc/Free、EnQue/DeQue 和队列状态解释。
<!-- cannbot:related:end -->
