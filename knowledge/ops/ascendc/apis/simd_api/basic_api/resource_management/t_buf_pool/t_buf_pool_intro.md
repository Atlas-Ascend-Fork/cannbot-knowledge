---
type: API
title: TBufPool简介
description: TPipe可以管理全局内存资源，而TBufPool可以手动管理或复用Unified Buffer/L1 Buffer物理内存，主要用于多个stage计算中Unified
  Buffer/L1 Buffer物理内存不足的场景。
tags: [task.lookup, topic.implementation.memory_management]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/resource_management/TBufPool/TBufPool_intro.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# TBufPool简介

TPipe可以管理全局内存资源，而TBufPool可以手动管理或复用Unified Buffer/L1 Buffer物理内存，主要用于多个stage计算中Unified Buffer/L1 Buffer物理内存不足的场景。

## 功能图示

下图展示了资源池划分的过程：

1.  通过TPipe::InitBuffer接口可以申请Buffer内存并使用队列进行管理；
2.  通过TPipe::InitBufPool可以划分出资源池BufPool1；
3.  通过TPipe::InitBufPool可以指定BufPool1与BufPool3地址和长度复用;
4.  通过TBufPool::InitBuffer及TBufPool::InitBufPool接口继续将BufPool1及BufPool3划分成Buffer或TBufPool资源池。

**图1**  BufPool资源池划分

如图示的嵌套关系，最外层TBufPool(BufPool1与BufPool3)需要通过TPipe::InitBufPool申请并初始化，内层TBufPool(BufPool2)可以通过TBufPool::InitBufPool申请并初始化。

## 约束说明

1.  TBufPool必须通过TPipe::InitBufPool或TBufPool::InitBufPool接口进行划分和初始化；资源池只能整体划分成部分，无法部分拼接为整体；
2.  不同TBufPool资源池切换进行计算时，需要调用TBufPool::Reset()接口清空已完成计算的TBufPool，清空后的TBufPool资源池及分配的Buffer和数据默认无效；
3.  不同资源池间分配的Buffer无法混用避免数据踩踏；
4.  AllocTensor/FreeTensor、EnQue/DeQue在切分TBufPool资源池时必须成对匹配使用，自动确保同步；
5.  切换资源池的时候，若手写同步，Ascend C不保证地址读写复用同步，因此不推荐手写同步。

<!-- cannbot:related:start -->
## 相关

- [507035 — 三队列 float32 tile 超 UB](../../../../../runbooks/compilation/507035_float32_tile_ub.md)（`exemplifies`）：TBufPool简介 与《507035 — 三队列 float32 tile 超 UB》的实质衔接是：TBufPool 在 TPipe 下手工复用 UB/L1，必须依次 InitBufPool、分配/取址、Reset 或 Destroy；所连容量和 TPipe 初始化案例直接约束资源预算与生命周期。
- [避免TPipe在对象内创建和初始化](../../../../../guides/operator_practice/simd_operator_optimization/overhead_optimization/avoid_tpipe_init_in_object.md)（`explains`）：TBufPool简介 与《避免TPipe在对象内创建和初始化》的实质衔接是：TBufPool 在 TPipe 下手工复用 UB/L1，必须依次 InitBufPool、分配/取址、Reset 或 Destroy；所连容量和 TPipe 初始化案例直接约束资源预算与生命周期。
- [Destroy](../t_pipe/destroy.md)（`same_topic`）：TBufPool简介 与《Destroy》的实质衔接是：TBufPool 在 TPipe 下手工复用 UB/L1，必须依次 InitBufPool、分配/取址、Reset 或 Destroy；所连容量和 TPipe 初始化案例直接约束资源预算与生命周期。
- [DestroyWithoutPipeAll](../t_pipe/destroy_without_pipe_all.md)（`same_topic`）：TBufPool简介 与《DestroyWithoutPipeAll》的实质衔接是：TBufPool 在 TPipe 下手工复用 UB/L1，必须依次 InitBufPool、分配/取址、Reset 或 Destroy；所连容量和 TPipe 初始化案例直接约束资源预算与生命周期。
- [ExternImplBufpool](../custom_t_buf_pool/extern_impl_bufpool.md)（`same_topic`）：TBufPool简介 与《ExternImplBufpool》的实质衔接是：TBufPool 在 TPipe 下手工复用 UB/L1，必须依次 InitBufPool、分配/取址、Reset 或 Destroy；所连容量和 TPipe 初始化案例直接约束资源预算与生命周期。
- [Init](../custom_t_buf_pool/init.md)（`same_topic`）：TBufPool简介 与《Init》的实质衔接是：TBufPool 在 TPipe 下手工复用 UB/L1，必须依次 InitBufPool、分配/取址、Reset 或 Destroy；所连容量和 TPipe 初始化案例直接约束资源预算与生命周期。
- [InitBufPool](init_buf_pool.md)（`same_topic`）：TBufPool简介 与《InitBufPool》的实质衔接是：TBufPool 在 TPipe 下手工复用 UB/L1，必须依次 InitBufPool、分配/取址、Reset 或 Destroy；所连容量和 TPipe 初始化案例直接约束资源预算与生命周期。
- [InitBufPool](../t_pipe/init_buf_pool.md)（`same_topic`）：TBufPool简介 与《InitBufPool》的实质衔接是：TBufPool 在 TPipe 下手工复用 UB/L1，必须依次 InitBufPool、分配/取址、Reset 或 Destroy；所连容量和 TPipe 初始化案例直接约束资源预算与生命周期。
- [InitBuffer](init_buffer.md)（`same_topic`）：TBufPool简介 与《InitBuffer》的实质衔接是：TBufPool 在 TPipe 下手工复用 UB/L1，必须依次 InitBufPool、分配/取址、Reset 或 Destroy；所连容量和 TPipe 初始化案例直接约束资源预算与生命周期。
- [Reset](../custom_t_buf_pool/reset.md)（`same_topic`）：TBufPool简介 与《Reset》的实质衔接是：TBufPool 在 TPipe 下手工复用 UB/L1，必须依次 InitBufPool、分配/取址、Reset 或 Destroy；所连容量和 TPipe 初始化案例直接约束资源预算与生命周期。
- [Reset](reset.md)（`same_topic`）：TBufPool简介 与《Reset》的实质衔接是：TBufPool 在 TPipe 下手工复用 UB/L1，必须依次 InitBufPool、分配/取址、Reset 或 Destroy；所连容量和 TPipe 初始化案例直接约束资源预算与生命周期。
- [TBufPool](t_buf_pool.md)（`same_topic`）：TBufPool简介 与《TBufPool》的实质衔接是：TBufPool 在 TPipe 下手工复用 UB/L1，必须依次 InitBufPool、分配/取址、Reset 或 Destroy；所连容量和 TPipe 初始化案例直接约束资源预算与生命周期。
- [TPipe](../t_pipe/t_pipe.md)（`same_topic`）：TBufPool简介 与《TPipe》的实质衔接是：TBufPool 在 TPipe 下手工复用 UB/L1，必须依次 InitBufPool、分配/取址、Reset 或 Destroy；所连容量和 TPipe 初始化案例直接约束资源预算与生命周期。
- [TPipe简介](../t_pipe/t_pipe_intro.md)（`same_topic`）：TBufPool简介 与《TPipe简介》的实质衔接是：TBufPool 在 TPipe 下手工复用 UB/L1，必须依次 InitBufPool、分配/取址、Reset 或 Destroy；所连容量和 TPipe 初始化案例直接约束资源预算与生命周期。
- [自定义TBufPool](../custom_t_buf_pool/custom_t_buf_pool.md)（`same_topic`）：焦点处理自定义 TBufPool 与基础 TBufPool 的资源池关系；TBufPool简介正文界定“TPipe可以管理全局内存资源，而TBufPool可以手动管理或复用Unified Buffer/L1 Buffer物理内存，主要用于多个stage计算中Unified Buffer/L1 Buffer物理内存不足的场景”。候选说明自定义 pool 如何建立在 TBufPool 的 InitBufPool/InitBuffer/Reset 生命周期上。
<!-- cannbot:related:end -->
