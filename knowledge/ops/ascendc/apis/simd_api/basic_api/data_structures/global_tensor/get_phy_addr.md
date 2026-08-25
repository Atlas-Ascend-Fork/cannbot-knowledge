---
type: API
title: GetPhyAddr
description: GlobalTensor::GetPhyAddr 接口，用于获取全局数据的物理地址，支持全平台。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/data_structures/GlobalTensor/GetPhyAddr.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# GetPhyAddr

GlobalTensor::GetPhyAddr 接口，用于获取全局数据的物理地址，支持全平台。

获取全局数据的地址。

本接口属于 GlobalTensor 数据结构操作接口，用于访问和修改 GM 上的 Tensor 属性。

返回值：全局数据的地址。

支持的硬件型号：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core。

<!-- cannbot:related:start -->
## 相关

- [Gather 双加 LocalTensor 基址导致交错旋转乱码](../../../../../runbooks/precision/localtensor_gather_base_address_not_double_counted.md)（`exemplifies`）：《Gather 双加 LocalTensor 基址导致交错旋转乱码》处理“Gather 已由 LocalTensor 提供源基址时，srcBaseAddr 再传物理地址会重复加基址；保持字节偏移并传 0 可恢复交错旋转。”。《GetPhyAddr》明确提供“GlobalTensor::GetPhyAddr 接口，用于获取全局数据的物理地址，支持全平台。”，其参数、调用或验证步骤直接接入Gather 的 base 地址、byte offset、重复偏移故障和地址计算合同。
- [GetPhyAddr const __gm__ 返回不可去 const](../../../../../runbooks/compilation/getphyaddr_const_gm_const.md)（`exemplifies`）：正式接口明确返回 const __gm__ 指针，是该编译错误的契约依据。
- [AscGetPhyStackBase](../../../c_api/sys_var/asc_get_phy_stack_base.md)（`related`）：AscGetPhyStackBase 与《GetPhyAddr》的实质衔接是：物理栈基地址与 Global/LocalTensor GetPhyAddr、物理 buffer 地址共同用于物理寻址；const GetPhyAddr 故障直接约束返回地址可变性。
- [GetPhyAddr](../local_tensor/get_phy_addr.md)（`same_topic`）：GetPhyAddr 的核心契约是“GlobalTensor::GetPhyAddr 接口，用于获取全局数据的物理地址，支持全平台”；GetPhyAddr 补充“返回LocalTensor的地址或指定偏移量后的地址”。
<!-- cannbot:related:end -->
