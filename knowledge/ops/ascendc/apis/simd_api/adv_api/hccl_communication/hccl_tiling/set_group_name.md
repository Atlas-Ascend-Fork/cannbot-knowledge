---
type: API
title: SetGroupName
description: 设置通信任务所在的通信域。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.data_movement.communication.collective_communication]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/HCCL_communication/HCCL_Tiling/SetGroupName.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# SetGroupName

设置通信任务所在的通信域。

参数：
- groupName（输入）：当前通信任务所在的通信域。string类型，支持的最大长度为128字节。

返回值：- 0表示设置成功。

<!-- cannbot:related:start -->
## 相关

- [GetHcclContext](../hccl_context/get_hccl_context.md)（`related`）：SetGroupName 与《GetHcclContext》的实质衔接是：SetGroupName 将通信域名称写入 HcclTilingData，再由 GetTiling 生成并通过 HcclContext 传入核侧；OpMC2Def 的 HcclGroup 是同一通信域契约的原型侧声明。
- [GetTiling](get_tiling.md)（`related`）：SetGroupName 与《GetTiling》的实质衔接是：SetGroupName 将通信域名称写入 HcclTilingData，再由 GetTiling 生成并通过 HcclContext 传入核侧；OpMC2Def 的 HcclGroup 是同一通信域契约的原型侧声明。
- [HCCL Tiling使用说明](hccl_tiling_usage.md)（`related`）：SetGroupName 与《HCCL Tiling使用说明》的实质衔接是：SetGroupName 将通信域名称写入 HcclTilingData，再由 GetTiling 生成并通过 HcclContext 传入核侧；OpMC2Def 的 HcclGroup 是同一通信域契约的原型侧声明。
- [HCCL Tiling构造函数](hccl_tiling_constructor.md)（`related`）：SetGroupName 与《HCCL Tiling构造函数》的实质衔接是：SetGroupName 将通信域名称写入 HcclTilingData，再由 GetTiling 生成并通过 HcclContext 传入核侧；OpMC2Def 的 HcclGroup 是同一通信域契约的原型侧声明。
- [HcclGroup（OpMC2Def）](../../../../utils_api/prototype_register_management/op_mc2_def/hccl_group.md)（`related`）：原型侧 HcclGroup 与运行时 tiling 的 SetGroupName 必须指向一致通信组，才能取得正确 context。
- [HcclTilingData](tiling_data_struct.md)（`related`）：SetGroupName 与《HcclTilingData》的实质衔接是：SetGroupName 将通信域名称写入 HcclTilingData，再由 GetTiling 生成并通过 HcclContext 传入核侧；OpMC2Def 的 HcclGroup 是同一通信域契约的原型侧声明。
- [SetHcclContext](../hccl_context/set_hccl_context.md)（`related`）：SetGroupName 与《SetHcclContext》的实质衔接是：SetGroupName 将通信域名称写入 HcclTilingData，再由 GetTiling 生成并通过 HcclContext 传入核侧；OpMC2Def 的 HcclGroup 是同一通信域契约的原型侧声明。
<!-- cannbot:related:end -->
