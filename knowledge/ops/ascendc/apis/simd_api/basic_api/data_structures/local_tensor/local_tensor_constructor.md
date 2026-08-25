---
type: API
title: LocalTensor构造函数
description: LocalTensor构造函数。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/data_structures/LocalTensor/LocalTensor_constructor.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# LocalTensor构造函数

两种形式：Pipe 编程框架下 `LocalTensor<T>()` 默认构造（不赋初值，通常由 TQue 分配，开发者不直接调用）；静态 Tensor 编程下 `LocalTensor<T>(TPosition pos, uint32_t addr, uint32_t tileSize)` 或 `LocalTensor<T>(uint32_t addr)` 指定逻辑位置/地址/长度构造。模板参数 T 为数据类型。

<!-- cannbot:related:start -->
## 相关

- [DataCopyPad 五参编译失败—LocalTensor 子视图替代偏移](../../../../../runbooks/compilation/datacopypad_offset_via_tensor_subview.md)（`exemplifies`）：《LocalTensor构造函数》处理“LocalTensor构造函数。”。《DataCopyPad 五参编译失败—LocalTensor 子视图替代偏移》明确“CANN 9.0.1 的 GM→UB DataCopyPad 不接收第五个目标偏移参数；先对 LocalTensor 取元素偏移子视图，再调用四参数重载。”，可直接用于核对LocalTensor 的默认/静态地址构造、LocalMemAllocator 构造路径及错误实参诊断。
- [DataCopyPad 无匹配重载 LocalTensor 实参不一致](../../../../../runbooks/compilation/datacopypad_localtensor.md)（`exemplifies`）：《LocalTensor构造函数》处理“LocalTensor构造函数。”。《DataCopyPad 无匹配重载 LocalTensor 实参不一致》明确“Ascend950（dav-3510）上 scatter kernel 把 reduce/CopyOut 缓冲声明为 LocalTensor<int8_t>、而 updates 队列产出 LocalTensor<T>，bisheng 编译报 no matching function for call to DataCopyPad/ApplyScatterReduce 并附 candidate not viable: no known conversion from LocalTensor<float> to const LocalTensor<int8_t>。判别方法：LocalTensor<E> 模板实参为强类型、E 不一致无隐式转换，DMA 重载全部 not viable。”，可直接用于核对LocalTensor 的默认/静态地址构造、LocalMemAllocator 构造路径及错误实参诊断。
- [L1/L0 tensor 须用 TPosition 构造非 SetAddr](../../../../../runbooks/compilation/l1_l0_tensor_tposition_setaddr.md)（`exemplifies`）：《LocalTensor构造函数》处理“LocalTensor构造函数。”。《L1/L0 tensor 须用 TPosition 构造非 SetAddr》明确“CANN 9.2.0 arch35 上 TBuf 无 SetAddr、LocalTensor<T>(addr) 触 tPos trait 错；L1/L0A/L0B/L0C 须用 LocalTensor<T>(TPosition, addr, size) 构造。”，可直接用于核对LocalTensor 的默认/静态地址构造、LocalMemAllocator 构造路径及错误实参诊断。
- [TBuf 不能直接传给 LocalTensor 形参](../../../../../runbooks/compilation/tbuf_gets_typed_localtensor_before_helper_call.md)（`exemplifies`）：《LocalTensor构造函数》处理“LocalTensor构造函数。”。《TBuf 不能直接传给 LocalTensor 形参》明确“Ascend C helper 以 LocalTensor 为形参时，调用点必须先从 TBuf 取得带类型的 LocalTensor，不能依赖隐式转换。”，可直接用于核对LocalTensor 的默认/静态地址构造、LocalMemAllocator 构造路径及错误实参诊断。
- [GetPosition](get_position.md)（`related`）：《GetPosition》处理“获取LocalTensor所在的TPosition逻辑位置，支持TPosition为VECIN、VECOUT、VECCALC、A1、A2、B1、B2、CO1、CO2。”。《LocalTensor构造函数》明确提供“LocalTensor构造函数。”，其参数、调用或验证步骤直接接入GetPosition 所读取的 LocalTensor 位置、构造来源和 TPosition 故障定位。
- [GetUserTag](get_user_tag.md)（`related`）：《GetUserTag》处理“获取指定Tensor块的Tag信息，用户可以根据Tag信息对Tensor进行不同操作。”。《LocalTensor构造函数》提供“LocalTensor构造函数。”，其具体合同或探针直接接入GetUserTag 与 SetUserTag 及 LocalTensor 所有权的读写合同。
- [LocalMemAllocatorConstructor](../../resource_management/local_mem_allocator/local_mem_allocator_constructor.md)（`related`）：《LocalTensor构造函数》处理“LocalTensor构造函数。”。《LocalMemAllocatorConstructor》明确“LocalMemAllocator构造函数，用于初始化指定物理位置的内存分配器对象。”，可直接用于核对LocalTensor 的默认/静态地址构造、LocalMemAllocator 构造路径及错误实参诊断。
- [LocalTensor简介](local_tensor_intro.md)（`same_topic`）：《LocalTensor构造函数》处理“LocalTensor构造函数。”。《LocalTensor简介》明确“LocalTensor表达AI Core中Local Memory（内部存储）内的L1/L0A/L0B/L0C Buffer及Unified Buffer中的数据。”，可直接用于核对LocalTensor 的默认/静态地址构造、LocalMemAllocator 构造路径及错误实参诊断。
<!-- cannbot:related:end -->
