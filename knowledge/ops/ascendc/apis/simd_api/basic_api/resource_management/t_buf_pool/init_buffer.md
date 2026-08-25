---
type: API
title: InitBuffer
description: 为TQue或TBuf进行内存分配，支持指定内存块个数和大小。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.memory_management]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/resource_management/TBufPool/InitBuffer.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---
# InitBuffer

头文件路径为："basic_api/kernel_tpipe.h"。

调用TBufPool::InitBuffer接口为TQue/TBuf进行内存分配。

参数：T: que参数的类型。；pos: Buffer逻辑位置，可以为VECIN、VECOUT、VECCALC、A1、B1、C1。关于TPosition的具体介绍请参考TPosition。

约束：声明TBufPool时，可以通过bufIDSize指定可分配Buffer的最大数量，默认上限为4，最大为16。TQue或TBuf的物理内存需要和TBufPool一致。

仅 Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 推理系列产品AI Core、Atlas 训练系列产品、Kirin X90、Kirin 9030 支持。

<!-- cannbot:related:start -->
## 相关

- [DoubleBuffer场景](../../../../../guides/operator_practice/simd_operator_impl/vector_programming/double_buffer_scenario.md)（`explains`）：DoubleBuffer场景 与《InitBuffer》的实质衔接是：DoubleBuffer 将主块拆为两份并通过 InitBuffer(...,2,...) 让搬入、计算、搬出重叠；主尾块切分材料说明尾块例外，UB 预算和 TQue/TBuf 重载故障直接约束 bufferNum 与长度配置。
- [AllocTensor](../t_que_bind/alloc_tensor.md)（`related`）：《AllocTensor》处理“从Que中分配Tensor，Tensor所占大小为InitBuffer时设置的每块内存长度。”。《InitBuffer》提供“为TQue或TBuf进行内存分配，支持指定内存块个数和大小。”，其具体合同或探针直接接入AllocTensor/FreeTensor 与 EnQue/DeQue 的队列所有权、初始化和耗尽故障。
- [Get](../t_buf/get.md)（`related`）：InitBuffer 为 TBuf 分配实际块大小，Get 返回的 LocalTensor 容量由该分配决定。
- [InitBufHandle](../t_que_bind/init_buf_handle.md)（`related`）：常规 TBufPool InitBuffer 直接为 TQue/TBuf 分配内存，而 InitBufHandle 是自定义池手工绑定路径，可据是否自主管理地址选择。
- [InitBufPool](../t_pipe/init_buf_pool.md)（`related`）：创建 TBufPool 后，InitBuffer 才从该池为 TQue/TBuf 分配具体 buffer，直接承接资源池初始化。
- [TBufConstructor](../t_buf/t_buf_constructor.md)（`related`）：TBuf 构造本身不分配容量，需由 InitBuffer 指定块大小后 Get 才可安全使用。
- [自定义TBufPool](../custom_t_buf_pool/custom_t_buf_pool.md)（`related`）：CustomTBufPool 提供外部/手动池管理；只有需要自定义地址布局时才替代普通 TBufPool。
- [InitBufPool](init_buf_pool.md)（`same_topic`）：InitBufPool 初始化池的地址范围，InitBuffer 再从池中为具体 TBuf/TQue 分配块，两者是分层分配链。
- [TBufPool](t_buf_pool.md)（`same_topic`）：TBufPool 类型页定义 InitBuffer 所操作的池对象和生命周期。
- [TBufPool](t_buf_pool_constructor.md)（`same_topic`）：构造池对象后必须 InitBufPool/InitBuffer 才有可用容量。
- [TBufPool简介](t_buf_pool_intro.md)（`same_topic`）：TBufPool简介 与《InitBuffer》的实质衔接是：TBufPool 在 TPipe 下手工复用 UB/L1，必须依次 InitBufPool、分配/取址、Reset 或 Destroy；所连容量和 TPipe 初始化案例直接约束资源预算与生命周期。
<!-- cannbot:related:end -->
