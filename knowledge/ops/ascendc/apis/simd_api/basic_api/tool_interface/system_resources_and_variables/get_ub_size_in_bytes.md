---
type: API
title: GetUBSizeInBytes
description: 获取UB空间的大小，单位为Byte。
tags: [task.lookup, topic.implementation.api_layer.basic_api]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/tool_interface/system_resources_and_variables/GetUBSizeInBytes.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# GetUBSizeInBytes

头文件路径为："basic_api/kernel_operator_sys_var_intf.h"。

获取UB空间的大小，单位为Byte。开发者根据UB的大小来计算循环次数等参数值。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [GatherV2 950 ACLNN 算子知识](../../../../../operators/aclnn/nn/index/gather_v2_950.md)（`related`）：“与 R-001 的行/列搬运相同，但分核与 `ubAvailable` 在 Device 用 `GetBlockNum/GetUBSizeInBytes-128KiB` 重算，避免 PCIe 地址由 SIMT 直接解引用。”记录 UB 可用量计算；“获取UB空间的大小，单位为Byte。开发者根据UB的大小来计算循环次数等参数值。”给出 GetUBSizeInBytes 的字节单位和用途，直接支撑减去 128 KiB 后的 buffer 分配。
<!-- cannbot:related:end -->
