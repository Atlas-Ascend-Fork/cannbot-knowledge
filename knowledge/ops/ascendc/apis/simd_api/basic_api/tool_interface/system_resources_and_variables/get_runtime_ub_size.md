---
type: API
title: GetRuntimeUBSize
description: 获取运行时UB空间的大小，单位为Byte。
tags: [task.lookup, topic.implementation.api_layer.basic_api]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/tool_interface/system_resources_and_variables/GetRuntimeUBSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# GetRuntimeUBSize

头文件路径为："basic_api/kernel_operator_sys_var_intf.h"。

获取运行时UB空间的大小，单位为Byte。开发者根据UB的大小来计算循环次数等参数值。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [GetUBSizeInBytes](get_ub_size_in_bytes.md)（`same_topic`）：两接口都返回当前核可用 UB 字节数；GetRuntimeUBSize 强调运行时查询，GetUBSizeInBytes 提供同一资源量的另一入口。
<!-- cannbot:related:end -->
