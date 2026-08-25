---
type: API
title: GetWithOffset
description: 以TBuf为基地址，向后偏移指定长度，将偏移后的地址作为起始地址，提取长度为指定值的Tensor。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.memory_management]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/resource_management/TBuf/GetWithOffset.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---
# GetWithOffset

头文件路径为："basic_api/kernel_tpipe.h"。

以TBuf为基地址，向后偏移指定长度，将偏移后的地址作为起始地址，提取长度为指定值的Tensor。

约束：size的数值是Tensor中元素的个数，size*sizeof(T) + bufOffset不能超过TBuf初始化时的长度。

bufOffset需满足32字节对齐的要求。

仅 Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 200I/500 A2 推理产品、Atlas 推理系列产品AI Core、Atlas 训练系列产品、Kirin X90、Kirin 9030 支持。

<!-- cannbot:related:start -->
## 相关

- [TBuf 不能直接传给 LocalTensor 形参](../../../../../runbooks/compilation/tbuf_gets_typed_localtensor_before_helper_call.md)（`exemplifies`）：GetWithOffset 在需要同一 TBuf 的带偏移 typed 视图时补全 Get<T>() 契约，可避免重新把 TBuf 或裸偏移直接传给 LocalTensor helper。
- [Vector Sub 源 UB 非 32B 对齐触发错误 340](../../../../../runbooks/compilation/vector_sub_ub_32b_340.md)（`exemplifies`）：Vector Sub 源 UB 非 32B 对齐触发错误 340 与《GetWithOffset》的实质衔接是：Vector Sub 的每个 UB 源必须 32B 对齐，LocalTensor 非零 operator[] 偏移会破坏对齐；Sub API、GetWithOffset/TBuf 和相邻未对齐故障卡直接支持定位及对齐搬入修法。
- [独立 TBuf.Get 返回重叠 UB 地址 dav-2201](../../../../../runbooks/compilation/tbuf_get_ub_dav_2201.md)（`exemplifies`）：推荐用一个大 TBuf 配合 GetWithOffset 划分不重叠子区，并强调 offset 是字节。
- [TBuf的使用](../../../../../guides/operator_practice/simd_operator_impl/vector_programming/tbuf_usage.md)（`explains`）：GetWithOffset 与《TBuf的使用》的实质衔接是：GetWithOffset 在 TBuf::Get 基础上增加 offset；TBuf 初始化长度、32B 对齐和重叠地址案例共同决定 size*sizeof(T)+offset 的合法范围。
- [SetAddrWithOffset](../../data_structures/local_tensor/set_addr_with_offset.md)（`related`）：SetAddrWithOffset 与《GetWithOffset》的实质衔接是：SetAddrWithOffset 与子视图/偏移接口共享元素偏移契约，所选故障卡直接说明错误基址叠加、L1/L0 限制及 DataCopy 偏移修复。
- [Get](get.md)（`same_topic`）：GetWithOffset 与《Get》的实质衔接是：GetWithOffset 在 TBuf::Get 基础上增加 offset；TBuf 初始化长度、32B 对齐和重叠地址案例共同决定 size*sizeof(T)+offset 的合法范围。
- [InitBuffer](../t_pipe/init_buffer.md)（`same_topic`）：GetWithOffset 与《InitBuffer》的实质衔接是：GetWithOffset 在 TBuf::Get 基础上增加 offset；TBuf 初始化长度、32B 对齐和重叠地址案例共同决定 size*sizeof(T)+offset 的合法范围。
- [TBufConstructor](t_buf_constructor.md)（`same_topic`）：GetWithOffset 与《TBufConstructor》的实质衔接是：GetWithOffset 在 TBuf::Get 基础上增加 offset；TBuf 初始化长度、32B 对齐和重叠地址案例共同决定 size*sizeof(T)+offset 的合法范围。
- [TBuf简介](t_buf_intro.md)（`same_topic`）：TBuf简介 与《GetWithOffset》的实质衔接是：TBuf 的构造、InitBuffer、Get/GetWithOffset 共同定义 UB 临时缓冲的分配与类型化取用；所连案例分别验证参数签名、地址独立性、容量预算和 helper 传参约束。
<!-- cannbot:related:end -->
