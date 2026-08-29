---
type: API
title: GetBlockNum
description: 获取当前任务配置的逻辑AI Core的数量，用于多核逻辑控制等。
tags: [task.lookup, topic.implementation.api_layer.basic_api]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/tool_interface/system_resources_and_variables/GetBlockNum.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---
# GetBlockNum

头文件路径为："basic_api/kernel_operator_sys_var_intf.h"。

获取当前任务配置的逻辑AI Core的数量，用于代码内部的多核逻辑控制等。

仅 Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 200I/500 A2 推理产品、Atlas 推理系列产品AI Core、Atlas 训练系列产品、Kirin X90、Kirin 9030 支持。

<!-- cannbot:related:start -->
## 相关

- [逐 block 串行启动退化多核并行](../../../../../runbooks/performance/block.md)（`exemplifies`）：改单次 `<<<numBlocks, nullptr, stream>>>` + kernel 内 `GetBlockIdx/GetBlockNum` 自算 `［startRow, endRow)` 后；获取当前任务配置的逻辑AI Core的数量，用于代码内部的多核逻辑控制等。；接口合同直接支撑修复后的 kernel 内多核行区间计算。
- [限制TilingData结构大小](../../../../../guides/operator_practice/simd_operator_optimization/overhead_optimization/limit_tiling_data_size.md)（`explains`）：“NumBlocks信息已经通过SetSimdNumBlocks接口进行设置，可以在Kernel侧调用GetBlockNum接口获取，无需通过TilingData结构传递。”；“获取当前任务配置的逻辑AI Core的数量，用于代码内部的多核逻辑控制等。”。Guide 给出删除冗余 NumBlocks 字段的具体替代调用，API 卡说明 GetBlockNum 返回的是任务逻辑核数。
- [GatherV2 950 ACLNN 算子知识](../../../../../operators/aclnn/nn/index/gather_v2_950.md)（`related`）：“与 R-001 的行/列搬运相同，但分核与 `ubAvailable` 在 Device 用 `GetBlockNum/GetUBSizeInBytes-128KiB` 重算，避免 PCIe 地址由 SIMT 直接解引用。”记录 GatherV2 PCIe 路线的实际调用；“获取当前任务配置的逻辑AI Core的数量，用于代码内部的多核逻辑控制等。”给出 GetBlockNum 的返回语义，直接支撑 Device 分核重算。
<!-- cannbot:related:end -->
