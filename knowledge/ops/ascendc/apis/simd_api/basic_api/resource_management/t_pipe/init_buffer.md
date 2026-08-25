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

- [507035 — 三队列 float32 tile 超 UB](../../../../../runbooks/compilation/507035_float32_tile_ub.md)（`exemplifies`）：507035 — 三队列 float32 tile 超 UB 与《InitBuffer》的实质衔接是：这些卡共享可复算的 UB 根因：队列/工作缓冲数量、对齐物理宽度或分块超过每核预算；TPipe InitBuffer是实际乘入 depth×bytes 的资源申请点。
- [TBuf 三参数 InitBuffer 触发 isTQue 静态断言](../../../../../runbooks/compilation/tbuf_initbuffer_uses_two_arguments.md)（`exemplifies`）：官方 InitBuffer API 明确同一接口为 TQue 和 TBuf 分配内存；与 focal 的编译器静态断言合读可定位到选错对象专用 overload，而非 UB 容量。
- [TQue InitBuffer 须传深度和 uint32 长度](../../../../../runbooks/compilation/tque_initbuffer_requires_depth_and_uint32_length.md)（`exemplifies`）：TPipe::InitBuffer API 明确列出 TQue 的 bufferNum 和 len 两个配置参数以及队列深度范围；Runbook 的编译修复正是该三参队列重载的实例。
- [未分配 TBuf 导致浮点索引随机错乱](../../../../../runbooks/precision/missing_tbuf_allocation_causes_undefined_ub_index_scratch.md)（`exemplifies`）：《未分配 TBuf 导致浮点索引随机错乱》处理“分支内使用未初始化的临时 TBuf 会造成静默索引错乱；在同一 Init 分支补齐 InitBuffer 后恢复精确结果。”。《InitBuffer》明确“用于为TQue等队列和TBuf分配内存。”，可直接用于核对TBuf 在同一分支先 InitBuffer 再 Get 的生命周期，以及无效/重叠 UB 地址的差分诊断。
- [独立 TBuf.Get 返回重叠 UB 地址 dav-2201](../../../../../runbooks/compilation/tbuf_get_ub_dav_2201.md)（`exemplifies`）：失败路径用 TPipe::InitBuffer 为八个独立 TBuf 各申请 8KB。
- [DoubleBuffer场景](../../../../../guides/operator_practice/simd_operator_impl/vector_programming/double_buffer_scenario.md)（`explains`）：DoubleBuffer场景 与《InitBuffer》的实质衔接是：DoubleBuffer 将主块拆为两份并通过 InitBuffer(...,2,...) 让搬入、计算、搬出重叠；主尾块切分材料说明尾块例外，UB 预算和 TQue/TBuf 重载故障直接约束 bufferNum 与长度配置。
- [TBuf的使用](../../../../../guides/operator_practice/simd_operator_impl/vector_programming/tbuf_usage.md)（`explains`）：指南初始化阶段调用 TPipe::InitBuffer 为两个 TBuf 分配 UB，是样例可运行的必要资源步骤。
- [TPipe和TQue编程范式](../../../../../guides/programming_guide/programming_model/ai_core_simd_programming/tpipe_tque_programming/tpipe_tque_paradigm.md)（`explains`）：《TPipe和TQue编程范式》说明上一章阐述了TPipe‑TQue编程模型的底层设计原理：基于经典C/C++队列管道（Queue Pipeline）思想，将算子任务拆分为多级流水Stage，依靠TQue队列解决写后读数据依赖、依靠AllocTensor/FreeTensor解决读后写内存复用冲突，通过底层同步指令实现多单元异步并行的时序安全。；《InitBuffer》说明用于为TQue等队列和TBuf分配内存。。二者在TPipe/TQue范式用InitBuffer和Alloc/EnQue/DeQue/FreeTensor表达内存所有权与Stage同步，相关FAQ和故障直接验证生命周期约束上存在可执行的直接衔接。
- [AllocTensor](../t_que/alloc_tensor.md)（`related`）：《InitBuffer》给出“用于为TQue等队列和TBuf分配内存。”；该约束/探针可直接复现、解释或前置验证《AllocTensor》中的“从Que中分配Tensor，Tensor大小为InitBuffer时设置的每块内存长度，支持non-inplace和inplace两种接口。”。
- [AllocTensor](../t_que_bind/alloc_tensor.md)（`related`）：《AllocTensor》处理“从Que中分配Tensor，Tensor所占大小为InitBuffer时设置的每块内存长度。”。《InitBuffer》提供“用于为TQue等队列和TBuf分配内存。”，其具体合同或探针直接接入AllocTensor/FreeTensor 与 EnQue/DeQue 的队列所有权、初始化和耗尽故障。
- [InitBufPool](init_buf_pool.md)（`related`）：InitBuffer 负责“用于为TQue等队列和TBuf分配内存”；InitBufPool 负责“初始化TBufPool内存资源池，适用于内存资源有限时手动指定UB/L1内存资源复用的场景”。
- [Reset](reset.md)（`related`）：InitBuffer 负责“用于为TQue等队列和TBuf分配内存”；Reset 负责“完成资源的释放与eventId等变量的初始化操作，恢复到TPipe的初始化状态”。
- [GetWithOffset](../t_buf/get_with_offset.md)（`same_topic`）：GetWithOffset 与《InitBuffer》的实质衔接是：GetWithOffset 在 TBuf::Get 基础上增加 offset；TBuf 初始化长度、32B 对齐和重叠地址案例共同决定 size*sizeof(T)+offset 的合法范围。
- [TBuf简介](../t_buf/t_buf_intro.md)（`same_topic`）：TBuf简介 与《InitBuffer》的实质衔接是：TBuf 的构造、InitBuffer、Get/GetWithOffset 共同定义 UB 临时缓冲的分配与类型化取用；所连案例分别验证参数签名、地址独立性、容量预算和 helper 传参约束。
<!-- cannbot:related:end -->
