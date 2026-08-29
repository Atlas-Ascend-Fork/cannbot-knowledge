---
type: API
title: Assert
description: SIMD和SIMT调试场景下提供assert断言功能，条件不为真时输出断言信息并终止算子运行。
tags: [task.lookup, topic.implementation.api_layer.utils_api]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/tuning_interface/assert.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# assert

本接口在SIMD和SIMT调试场景下提供assert断言功能。在算子Kernel侧的实现代码中，如果assert的内部条件判断不为真，则会输出assert条件，并将输入的信息格式化打印在屏幕上，同时算子运行失败。

在算子Kernel侧代码的适当位置使用assert进行断言检查，并格式化输出一些调试信息。示例如下：

打印信息示例如下：

请注意，assert接口的打印功能对算子的实际运行性能有影响。

函数原型：assert(expr)

参数：expr（输入）：assert断言是否终止程序的条件。条件为true则程序继续执行，条件为false则终止程序。

返回值：无

平台支持：Ascend 950PR/950DT、Atlas A3 训练/推理、Atlas A2 训练/推理系列支持，其他产品不支持。
约束：-   该接口当前仅支持融合编译场景。
-   SIMD场景，如果开发者需要包含标准库头文件，请在"utils/debug/asc_assert.h"头文件之前包含，避免assert符号冲突。

-   SIMT场景的支持情况如下：

    - Ascend 950PR/Ascend 950DT：支持。
需包含头文件 "utils/debug/asc_assert.h"。
支持 SIMT 与 SIMD/SIMT 混合编程场景。
