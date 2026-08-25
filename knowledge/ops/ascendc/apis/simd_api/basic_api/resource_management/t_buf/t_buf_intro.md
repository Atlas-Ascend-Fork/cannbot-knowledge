---
type: API
title: TBuf简介
description: 使用Ascend C编程的过程中，可能会用到一些临时变量。这些临时变量占用的内存可以使用TBuf数据结构来管理，存储位置通过模板参数来设置，可以设置为不同的TPosition逻辑位置。
tags: [task.lookup, topic.implementation.memory_management]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/resource_management/TBuf/TBuf_intro.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# TBuf简介

使用Ascend C编程的过程中，可能会用到一些临时变量。这些临时变量占用的内存可以使用TBuf数据结构来管理，存储位置通过模板参数来设置，可以设置为不同的TPosition逻辑位置。

TBuf继承自TQueBind父类，继承关系如下：

TBuf占用的存储空间通过TPipe进行管理，您可以通过InitBuffer接口为TBuf进行内存初始化操作，之后即可通过Get获取指定长度的Tensor参与计算。

使用InitBuffer为TBuf分配内存和为队列分配内存有以下差异：

-   为TBuf分配的内存空间只能参与计算，无法执行队列的入队出队操作。
-   调用一次内存初始化接口，TPipe只会为TBuf分配一块内存，为队列可以通过参数设置申请多块内存。如果要使用多个临时变量，需要定义多个TBuf数据结构，对每个TBuf数据结构分别调用InitBuffer接口进行内存初始化。
-   TBuf获取的Tensor无需释放。

<!-- cannbot:related:start -->
## 相关

- [507035 — 三队列 float32 tile 超 UB](../../../../../runbooks/compilation/507035_float32_tile_ub.md)（`exemplifies`）：TBuf简介 与《507035 — 三队列 float32 tile 超 UB》的实质衔接是：TBuf 的构造、InitBuffer、Get/GetWithOffset 共同定义 UB 临时缓冲的分配与类型化取用；所连案例分别验证参数签名、地址独立性、容量预算和 helper 传参约束。
- [InitOutput GM 专用，UB 清零用 Duplicate](../../../../../runbooks/compilation/initoutput_gm_ub_duplicate.md)（`exemplifies`）：InitOutput GM 专用，UB 清零用 Duplicate 与《TBuf简介》的实质衔接是：InitOutput 只接受 GM GlobalTensor，而 UB LocalTensor 要用 Duplicate；相关 API、类型错误、TBuf 取 LocalTensor 和清零覆盖故障直接验证该边界。
- [SIMT __ubuf__ 静态数组 UB 占用不随分支释放](../../../../../runbooks/compilation/simt_ubuf_ub.md)（`exemplifies`）：《SIMT __ubuf__ 静态数组 UB 占用不随分支释放》说明SIMT kernel 的 __ubuf__ 静态数组是编译期分配、生命周期绑所在函数栈的 UB 资源，运行时分支只控制是否解引用、不控制是否占用；把“需要该数组”与“不需要该数组”两条路径塞进同一函数，会令不解引用的路径也白白占住 UB。给出按解引用关系拆函数的判别方法。；《TBuf简介》说明使用Ascend C编程的过程中，可能会用到一些临时变量。这些临时变量占用的内存可以使用TBuf数据结构来管理，存储位置通过模板参数来设置，可以设置为不同的TPosition逻辑位置。。二者在SIMT静态__ubuf__数组按函数栈常驻，地址空间限定、UB预算及TBuf管理方案直接决定如何拆函数或改为受管内存上存在可执行的直接衔接。
- [TBuf 三参数 InitBuffer 触发 isTQue 静态断言](../../../../../runbooks/compilation/tbuf_initbuffer_uses_two_arguments.md)（`exemplifies`）：TBuf简介 与《TBuf 三参数 InitBuffer 触发 isTQue 静态断言》的实质衔接是：TBuf 的构造、InitBuffer、Get/GetWithOffset 共同定义 UB 临时缓冲的分配与类型化取用；所连案例分别验证参数签名、地址独立性、容量预算和 helper 传参约束。
- [TBuf 不能直接传给 LocalTensor 形参](../../../../../runbooks/compilation/tbuf_gets_typed_localtensor_before_helper_call.md)（`exemplifies`）：TBuf简介 与《TBuf 不能直接传给 LocalTensor 形参》的实质衔接是：TBuf 的构造、InitBuffer、Get/GetWithOffset 共同定义 UB 临时缓冲的分配与类型化取用；所连案例分别验证参数签名、地址独立性、容量预算和 helper 传参约束。
- [arch35 小 per-channel 输出读旧值判别与规避](../../../../../runbooks/compilation/arch35_per_channel.md)（`exemplifies`）：《arch35 小 per-channel 输出读旧值判别与规避》处理“arch35 上 DCCI 缓存不一致使 DataCopyPad 对小 per-channel [C] 输出不可靠、TQue GetValue(MTE2→scalar) 读到旧值；判别方法为先 V-launder(Duplicate 0.0f+Add) 到 TBuf 再 GetValue，并用 GlobalTensor::SetValue 直写 GM per-channel 结果。”。《TBuf简介》提供“使用Ascend C编程的过程中，可能会用到一些临时变量。这些临时变量占用的内存可以使用TBuf数据结构来管理，存储位置通过模板参数来设置，可以设置为不同的TPosition逻辑位置。”，其具体合同或探针直接接入arch35 小 per-channel 的 DCCI/Scalar 旧值机制、V-launder 与 SetValue 验证。
- [按 dtype 分配 UB 必须匹配 tiling 预算](../../../../../runbooks/compilation/dtype_conditional_ub_allocation_matches_tiling_budget.md)（`exemplifies`）：TBuf简介 与《按 dtype 分配 UB 必须匹配 tiling 预算》的实质衔接是：TBuf 的构造、InitBuffer、Get/GetWithOffset 共同定义 UB 临时缓冲的分配与类型化取用；所连案例分别验证参数签名、地址独立性、容量预算和 helper 传参约束。
- [未分配 TBuf 导致浮点索引随机错乱](../../../../../runbooks/precision/missing_tbuf_allocation_causes_undefined_ub_index_scratch.md)（`exemplifies`）：TBuf简介 与《未分配 TBuf 导致浮点索引随机错乱》的实质衔接是：TBuf 的构造、InitBuffer、Get/GetWithOffset 共同定义 UB 临时缓冲的分配与类型化取用；所连案例分别验证参数签名、地址独立性、容量预算和 helper 传参约束。
- [独立 TBuf.Get 返回重叠 UB 地址 dav-2201](../../../../../runbooks/compilation/tbuf_get_ub_dav_2201.md)（`exemplifies`）：TBuf简介 与《独立 TBuf.Get 返回重叠 UB 地址 dav-2201》的实质衔接是：TBuf 的构造、InitBuffer、Get/GetWithOffset 共同定义 UB 临时缓冲的分配与类型化取用；所连案例分别验证参数签名、地址独立性、容量预算和 helper 传参约束。
- [TBuf的使用](../../../../../guides/operator_practice/simd_operator_impl/vector_programming/tbuf_usage.md)（`explains`）：TBuf简介 与《TBuf的使用》的实质衔接是：TBuf 的构造、InitBuffer、Get/GetWithOffset 共同定义 UB 临时缓冲的分配与类型化取用；所连案例分别验证参数签名、地址独立性、容量预算和 helper 传参约束。
- [Get](get.md)（`same_topic`）：TBuf简介 与《Get》的实质衔接是：TBuf 的构造、InitBuffer、Get/GetWithOffset 共同定义 UB 临时缓冲的分配与类型化取用；所连案例分别验证参数签名、地址独立性、容量预算和 helper 传参约束。
- [GetWithOffset](get_with_offset.md)（`same_topic`）：TBuf简介 与《GetWithOffset》的实质衔接是：TBuf 的构造、InitBuffer、Get/GetWithOffset 共同定义 UB 临时缓冲的分配与类型化取用；所连案例分别验证参数签名、地址独立性、容量预算和 helper 传参约束。
- [InitBuffer](../t_pipe/init_buffer.md)（`same_topic`）：TBuf简介 与《InitBuffer》的实质衔接是：TBuf 的构造、InitBuffer、Get/GetWithOffset 共同定义 UB 临时缓冲的分配与类型化取用；所连案例分别验证参数签名、地址独立性、容量预算和 helper 传参约束。
- [TBuf](t_buf.md)（`same_topic`）：TBuf简介 与《TBuf》的实质衔接是：TBuf 的构造、InitBuffer、Get/GetWithOffset 共同定义 UB 临时缓冲的分配与类型化取用；所连案例分别验证参数签名、地址独立性、容量预算和 helper 传参约束。
- [TBufConstructor](t_buf_constructor.md)（`same_topic`）：TBuf简介 与《TBufConstructor》的实质衔接是：TBuf 的构造、InitBuffer、Get/GetWithOffset 共同定义 UB 临时缓冲的分配与类型化取用；所连案例分别验证参数签名、地址独立性、容量预算和 helper 传参约束。
<!-- cannbot:related:end -->
