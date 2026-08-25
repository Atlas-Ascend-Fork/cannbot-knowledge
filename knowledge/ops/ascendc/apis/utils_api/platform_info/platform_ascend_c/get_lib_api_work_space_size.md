---
type: API
title: GetLibApiWorkSpaceSize
description: 获取AscendC API需要的workspace空间大小。
tags: [task.lookup, topic.implementation.api_layer.utils_api, topic.programming_model.system_variable]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/platform_info/PlatformAscendC/GetLibApiWorkSpaceSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# GetLibApiWorkSpaceSize

## 功能说明
获取AscendC API需要的workspace空间大小。
## 函数原型
## 参数说明
无
## 返回值说明
返回uint32_t数据类型的结果，该结果代表当前系统workspace的大小，单位为字节。
## 约束说明
无

<!-- cannbot:related:start -->
## 相关

- [使用高阶API时配套的Tiling实现](../../../../guides/programming_guide/advanced_programming/aclnn_operator_development/design_and_implementation/tiling_with_advanced_api.md)（`explains`）：指南明确即使算子没有自定义临时数据，也要用 GetLibApiWorkSpaceSize 查询高阶 API 的系统 workspace 后再设置 Context。
- [如何使用workspace](../../../../guides/programming_guide/appendix/common_operations/how_to_use_workspace.md)（`explains`）：workspace 指南给出 host 分配、地址下发和 kernel 使用流程，补全 GetLibApiWorkSpaceSize 只有返回字节数而没有生命周期的部分。
- [SetSysWorkSpace](../../../simd_api/basic_api/resource_management/workspace/set_sys_work_space.md)（`same_topic`）：SetSysWorkSpace 与《GetLibApiWorkSpaceSize》的实质衔接是：SetSysWorkSpace 设置高阶 API 的系统区指针；Host 先用 GetLibApiWorkSpaceSize 计量，kernel 再经 GetSys/GetUserWorkspace 分区，RESERVED 故障验证偏移契约。
<!-- cannbot:related:end -->
