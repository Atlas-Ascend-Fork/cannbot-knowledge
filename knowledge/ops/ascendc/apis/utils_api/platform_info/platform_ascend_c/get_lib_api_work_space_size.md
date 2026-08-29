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

- [GetSysWorkSpacePtr](../../../simd_api/basic_api/resource_management/workspace/get_sys_work_space_ptr.md)（`related`）：获取AscendC API需要的workspace空间大小。；获取系统workspace指针。部分高阶API如Matmul需要使用系统workspace，相关接口需要传入系统workspace指针，此时可以通过该接口获取。使用系统workspace时，host侧开发者需要自行申请系统workspace的空间，其预留空间大小可以通过GetLibApiWorkSpaceSize接口获取。。GetLibApiWorkSpaceSize 给出 Host 侧预留容量，GetSysWorkSpacePtr 明确该容量由 Host 申请后在 Kernel 侧取得系统 workspace 指针，二者是同一 workspace 生命周期的容量端与地址端。
<!-- cannbot:related:end -->
