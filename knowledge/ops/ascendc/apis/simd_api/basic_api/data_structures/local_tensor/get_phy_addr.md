---
type: API
title: GetPhyAddr
description: 返回LocalTensor的地址或指定偏移量后的地址。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/data_structures/LocalTensor/GetPhyAddr.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# GetPhyAddr

返回LocalTensor的地址或指定偏移量后的地址。

返回LocalTensor的地址或指定偏移量后的地址。

本接口属于 LocalTensor 数据结构操作接口，用于访问和修改 UB 上的 Tensor 属性。

返回值：LocalTensor的地址或指定偏移量后的地址。

支持的硬件型号：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core。

<!-- cannbot:related:start -->
## 相关

- [Gather 双加 LocalTensor 基址导致交错旋转乱码](../../../../../runbooks/precision/localtensor_gather_base_address_not_double_counted.md)（`exemplifies`）：《Gather 双加 LocalTensor 基址导致交错旋转乱码》处理“Gather 已由 LocalTensor 提供源基址时，srcBaseAddr 再传物理地址会重复加基址；保持字节偏移并传 0 可恢复交错旋转。”。《GetPhyAddr》明确提供“返回LocalTensor的地址或指定偏移量后的地址。”，其参数、调用或验证步骤直接接入Gather 的 base 地址、byte offset、重复偏移故障和地址计算合同。
- [Reg LoadAlign 不接受 const __ubuf__ 指针](../../../../../runbooks/compilation/reg_loadalign_requires_nonconst_ubuf_pointer.md)（`exemplifies`）：《Reg LoadAlign 不接受 const __ubuf__ 指针》给出“CANN 9.0.1 RegBase 的两参数 LoadAlign/StoreAlign 要求非 const UB 指针；const 会让 VF 封装与 asc_vf_call 编译失败。”；该约束/探针可直接复现、解释或前置验证《GetPhyAddr》中的“返回LocalTensor的地址或指定偏移量后的地址。”。
- [__aicore__ 禁止 void* 转 __ubuf__ 桥接](../../../../../runbooks/compilation/aicore_void_ubuf.md)（`exemplifies`）：《GetPhyAddr》明确“返回LocalTensor的地址或指定偏移量后的地址。”；它与《__aicore__ 禁止 void* 转 __ubuf__ 桥接》的“dav-3510 上为混合 dtype Reg wrapper 用 void* 形参 + 内部 (__ubuf__ T*) 强转桥接 LocalTensor<half> 与 LocalTensor<float>，编译报 casting 'void *' to type '__ubuf__' not allowed in aicore function（5 处）；void* 桥接路线 banned，须改 const LocalTensor<T>& 形参 + 内部 GetPhyAddr()。”在实际调用参数、数据流或结果校验上直接衔接。
- [__ubuf__ 指针传普通形参导致编译失败](../../../../../runbooks/compilation/ubuf_pointer_preserves_address_space.md)（`exemplifies`）：《__ubuf__ 指针传普通形参导致编译失败》给出“Ascend C 地址空间是类型的一部分；__ubuf__ 指针不能隐式绑定到普通 T* 形参，未使用参数应删除或按真实地址空间声明。”；该约束/探针可直接复现、解释或前置验证《GetPhyAddr》中的“返回LocalTensor的地址或指定偏移量后的地址。”。
- [AscGetPhyStackBase](../../../c_api/sys_var/asc_get_phy_stack_base.md)（`related`）：AscGetPhyStackBase 与《GetPhyAddr》的实质衔接是：物理栈基地址与 Global/LocalTensor GetPhyAddr、物理 buffer 地址共同用于物理寻址；const GetPhyAddr 故障直接约束返回地址可变性。
- [GetPhyAddr](../global_tensor/get_phy_addr.md)（`same_topic`）：GetPhyAddr 的核心契约是“GlobalTensor::GetPhyAddr 接口，用于获取全局数据的物理地址，支持全平台”；GetPhyAddr 补充“返回LocalTensor的地址或指定偏移量后的地址”。
<!-- cannbot:related:end -->
