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
