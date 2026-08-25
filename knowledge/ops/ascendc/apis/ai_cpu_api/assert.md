---
type: API
title: assert（AI CPU API）
description: 该接口实现AI CPU算子Kernel调试场景下的assert断言功能。 算子执行中，如果assert内部条件判断不为真，则输出assert条件、触发文件名、行号等信息。
tags: [task.lookup, topic.implementation.api_layer.aicpu_api]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/AI-CPU-API/assert.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---


# assert（AI CPU API）

该接口实现AI CPU算子Kernel调试场景下的assert断言功能。 算子执行中，如果assert内部条件判断不为真，则输出assert条件、触发文件名、行号等信息。

参数：
- expr（输入）：assert断言是否终止程序的条件。为true则程序继续执行，为false则终止程序。

约束：
- 该接口仅支持通过>>调用，并在异构编译场景使用。
- kernel开发不要包含系统的assert.h，会导致宏定义冲突。
- assert接口调用形式与C语言一致，不需要使用AscendC命名空间。
- 该接口使用Dump功能，所有使用Dump功能的接口在每个核上Dump的数据总量不可超过1M。请开发者自行控制待打印的内容数据量，超出则不会打印。
- 使用该接口时，若采用bisheng命令行编译，开发者需要手动链接相关的静态库；而使用CMake编译时，框架会自动处理链接问题，无需开发者额外关注。具体编译命令如下：通过--cce-aicpu-laicpu_api为Device链接libaicpu_api.a，通过--cce-aicpu-L指定libaicpu_api.a的库路径。

支持：Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品。不支持：Atlas 200I/500 A2 推理产品、Atlas 推理系列产品AI Core、Atlas 推理系列产品Vector Core、Atlas 训练系列产品。

<!-- cannbot:related:start -->
## 相关

- [AI CPU算子编译](../../guides/programming_guide/compilation_and_execution/operator_compilation/ai_cpu_operator_compilation.md)（`explains`）：assert 依赖 AI CPU 的 .aicpu/.asc 双文件编译、`>>` 调用和 libaicpu_api.a 链接；编译指南给出这些落地步骤。
- [AI CPU编程（编程模型）](../../guides/programming_guide/programming_model/ai_cpu_programming.md)（`explains`）：AI CPU 编程模型解释 `.aicpu` 核函数如何由 `.asc` 中的 `>>` 入口调用，补全 assert 所在的设备执行域。
- [Assert](../simd_api/basic_api/debug_interface/exception_detection/assert.md)（`related`）：两卡都以条件失败触发设备侧诊断，但目标接口运行在 SIMD/SIMT AI Core 域；对照可防止把 AI CPU 断言的链接和调用规则套到 AI Core。
- [Assert](../utils_api/tuning_interface/assert.md)（`related`）：Utils 调测断言覆盖 SIMD/SIMT 融合编译场景，而 AI CPU assert 覆盖 AI CPU Kernel；二者形成按执行域选择断言接口的边界。
<!-- cannbot:related:end -->
