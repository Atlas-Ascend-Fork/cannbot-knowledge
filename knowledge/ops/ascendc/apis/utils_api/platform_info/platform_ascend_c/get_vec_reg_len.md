---
type: API
title: GetVecRegLen
description: 获取当前硬件平台芯片架构Vec计算单元位宽。
tags: [task.lookup, topic.implementation.api_layer.utils_api, topic.programming_model.system_variable]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/platform_info/PlatformAscendC/GetVecRegLen.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# GetVecRegLen

## 功能说明
获取当前硬件平台芯片架构Vec计算单元位宽。
## 函数原型
## 参数说明
无
## 返回值
-   对于RegBase硬件平台芯片架构，返回当前硬件平台Vector计算单元位宽。
-   对于非RegBase硬件平台芯片架构，返回0 。
## 约束说明
无

<!-- cannbot:related:start -->
## 相关

- [AscGetVfLen](../../../simd_api/c_api/sys_var/asc_get_vf_len.md)（`related`）：AscGetVfLen 在 Kernel C API 中返回 VL，GetVecRegLen 在 Host 平台信息中返回同一 Vector 单元位宽；二者衔接 Host 规划与 Device 分块。
- [GetVecLen](../../../simd_api/basic_api/tool_interface/system_resources_and_variables/get_vec_len.md)（`related`）：GetVecLen 在 Device 侧读取 RegTensor VL，GetVecRegLen 在 Host 平台信息侧查询向量寄存器位宽；Host Tiling 与 Kernel 循环需保持一致。
<!-- cannbot:related:end -->
