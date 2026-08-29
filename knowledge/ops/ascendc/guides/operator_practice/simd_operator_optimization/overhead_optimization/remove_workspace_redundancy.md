---
type: Guide
title: 核函数内删除Workspace相关冗余操作
description: 【描述】在Ascend C算子工程中，编写核函数时传入的参数workspace已经直接赋值为用户Workspace，因此无需再通过SetSysWorkspace和GetUserWorkspace来设置和获取Workspace。减少这些冗余判断后，编译器可以在不使用该参数的情况下进一步优化未用到的workspace变量。
tags: [task.lookup, topic.performance.optimization.optimization_overview]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/operator_practice/simd_operator_optimization/overhead_optimization/remove_workspace_redundancy.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 核函数内删除Workspace相关冗余操作

【优先级】中
【描述】在Ascend C算子工程中，编写核函数时传入的参数workspace已经直接赋值为用户Workspace，因此无需再通过SetSysWorkspace和GetUserWorkspace来设置和获取Workspace。减少这些冗余判断后，编译器可以在不使用该参数的情况下进一步优化未用到的workspace变量。
【反例】
fast_gelu函数的参数workspace等价于用户workspace，且不为空，仍然对workspace进行判空，并且设置SetSysWorkspace和GetUserWorkspace来获取用户Workspace。
【正例】
fast_gelu函数中删除对workspace参数进行空指针判断，也无需设置SetSysWorkspace和通过GetUserWorkspace来获取Workspace。

<!-- cannbot:related:start -->
## 相关

- [SetSysWorkSpace](../../../../apis/simd_api/basic_api/resource_management/workspace/set_sys_work_space.md)（`explains`）：“在Ascend C算子工程中，编写核函数时传入的参数workspace已经直接赋值为用户Workspace，因此无需再通过SetSysWorkspace和GetUserWorkspace来设置和获取Workspace。”与“框架需要使用的workspace称之为系统workspace。Matmul Kernel侧接口等高阶API需要系统workspace，所以在使用该类API时，需要调用该接口，设置系统workspace的指针。”分别给出双端正文事实；优化指南区分用户 workspace 的冗余设置与高阶 API 需要的系统 workspace，SetSysWorkSpace 卡给出后一类调用条件，二者形成删除冗余而保留必要设置的决策边界。
<!-- cannbot:related:end -->
