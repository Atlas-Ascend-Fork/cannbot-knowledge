---
type: API
title: AscGetVfLen
description: 获取Tensor位宽VL的大小。
tags: [task.lookup, topic.programming_model.system_variable]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/sys_var/asc_get_vf_len.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# AscGetVfLen

获取Tensor位宽VL（Vector Length）的大小。
函数原型：constexpr int64_t asc_get_vf_len()
返回值：位宽VL（Vector Length）的大小。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [GetVecRegLen](../../../utils_api/platform_info/platform_ascend_c/get_vec_reg_len.md)（`related`）：AscGetVfLen 在 Kernel C API 中返回 VL，GetVecRegLen 在 Host 平台信息中返回同一 Vector 单元位宽；二者衔接 Host 规划与 Device 分块。
- [系统变量](system_variables.md)（`related`）：系统变量索引明确列出 AscGetVfLen，用于取得当前 VF 的向量长度并支撑分块循环。
<!-- cannbot:related:end -->
