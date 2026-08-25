---
type: API
title: GetArchVersion
description: 获取当前AI处理器架构版本号。
tags: [task.lookup, topic.implementation.api_layer.basic_api]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/tool_interface/system_resources_and_variables/GetArchVersion.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---
# GetArchVersion

头文件路径为："basic_api/kernel_operator_sys_var_intf.h"。

获取当前AI处理器架构版本号。

参数：coreVersion(输出): AI处理器架构版本。

仅 Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 200I/500 A2 推理产品、Atlas 推理系列产品AI Core、Atlas 训练系列产品 支持。

<!-- cannbot:related:start -->
## 相关

- [AscGetArchVer](../../../c_api/sys_var/asc_get_arch_ver.md)（`same_topic`）：《AscGetArchVer》明确“获取当前AI处理器架构版本号。”；它与《GetArchVersion》的“获取当前AI处理器架构版本号。”在实际调用参数、数据流或结果校验上直接衔接。
<!-- cannbot:related:end -->
