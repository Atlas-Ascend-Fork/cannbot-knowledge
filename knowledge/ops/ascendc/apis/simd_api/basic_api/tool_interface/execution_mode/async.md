---
type: API
title: Async
description: 通过模板函数封装AIC与AIV分离模式的硬件条件分支，在指定执行单元下执行特定函数，避免代码中显式使用硬件条件分支。
tags: [task.lookup, topic.implementation.api_layer.basic_api]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/tool_interface/execution_mode/Async.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---
# Async

头文件路径为："basic_api/kernel_operator_utils_intf.h"。

基于分离模式（AIC和AIV分离）开发融合算子时，算子逻辑中通常同时包含AIV和AIC的处理逻辑，此时需要使用Ascend C提供的宏ASCEND_IS_AIV/ASCEND_IS_AIC实现如下硬件条件分支来对AIV和AIC的代码进行隔离
Async通过模板函数的方式对这种隔离模式进行了封装，提供了一个统一的接口，用于在不同执行单元（AIC或AIV）下执行特定函数，从而避免在代码中使用硬件条件分支。

参数：engine: EngineType枚举类型，可取值如下，对应不同的硬件执行单元： &bull; AIC  &bull; AIV；funPtr: 函数指针，指定要执行的函数，函数签名和参数类型由class... Args决定。；class... Args: 可变参数模板，表示函数参数的类型列表，用于传递给funPtr。；Args... args(输入): 与class... Args对应的参数列表，表示传递给funPtr的实际参数。

仅 Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品 支持。

<!-- cannbot:related:start -->
## 相关

- [arch35 __aicore__ 调 LocalMemBar 报 507035](../../../../../runbooks/compilation/arch35_aicore_localmembar_507035.md)（`exemplifies`）：《arch35 __aicore__ 调 LocalMemBar 报 507035》处理“Ascend950PR (arch35/dav_c310) 上 Reg::LocalMemBar<VEC_STORE,VEC_LOAD> 是 __simd_callee__ 函数，须在 __simd_vf__ (VF) 调用上下文内使用；从常规 __aicore__ kernel 函数直接调用触发运行时 507035 (AIV 错误)。本 trace 两次独立调用（旧 4-buffer 代码、新 5-buffer 重排代码）均 507035。作为 count-based Compare→Select mask 隐患的最小 sync 修复手段 banned。”。《Async》明确提供“通过模板函数封装AIC与AIV分离模式的硬件条件分支，在指定执行单元下执行特定函数，避免代码中显式使用硬件条件分支。”，其参数、调用或验证步骤直接接入LocalMemBar 507035 的 Compare/Select 调用触发、屏障约束和可执行替代。
<!-- cannbot:related:end -->
