---
type: API
title: GetVecLen
description: 获取RegTensor位宽VL（Vector Length）的大小。
tags: [task.lookup, topic.implementation.api_layer.basic_api]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/tool_interface/system_resources_and_variables/GetVecLen.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# GetVecLen

头文件路径为："basic_api/kernel_operator_sys_var_intf.h"。

获取RegTensor位宽VL（Vector Length）的大小。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [GetVecRegLen](../../../../utils_api/platform_info/platform_ascend_c/get_vec_reg_len.md)（`related`）：GetVecLen 在 Device 侧读取 RegTensor VL，GetVecRegLen 在 Host 平台信息侧查询向量寄存器位宽；Host Tiling 与 Kernel 循环需保持一致。
<!-- cannbot:related:end -->
