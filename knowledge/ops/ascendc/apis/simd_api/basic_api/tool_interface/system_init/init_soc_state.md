---
type: API
title: InitSocState
description: 初始化AI Core全局状态，包括AIC与AIV的公共状态及各自特有状态；不同产品实际执行的初始化项存在差异。
tags: [task.lookup, topic.implementation.api_layer.basic_api]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/tool_interface/system_init/InitSocState.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---
# InitSocState

头文件路径为："basic_api/kernel_operator_common_intf.h"。

本接口对AI Core的全局状态进行初始化，包括AIC（Cube Core）与AIV（Vector Core）的公共状态及各自特有状态。由于不同产品的实现存在差异，实际执行的初始化项也有所不同。

接口涉及的全部初始化操作汇总
各产品实际执行的初始化项

约束：- 在实际运行中，这些值可能被前序执行的算子修改，若不调用该接口进行初始化，非预期的值可能导致计算结果出现精度错误。

  例如前序算子使用Counter模式但未重置为Normal模式，当前算子以默认的Normal模式设置Mask时，会导致Mask设置不符合预期，进而引发精度错误。
- 在TPipe框架编程中，初始化过程由TPipe完成，无需开发者关注；在静态Tensor编程的场景中，用户必须在Kernel入口处调用此函数来初始化AI Core状态。

仅 Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 推理系列产品AI Core、Atlas 推理系列产品Vector Core 支持。

<!-- cannbot:related:start -->
## 相关

- [系统初始化](system_init.md)（`related`）：《InitSocState》的任务是“初始化AI Core全局状态，包括AIC与AIV的公共状态及各自特有状态；不同产品实际执行的初始化项存在差异。”。《系统初始化》具体提供“系统初始化接口索引页，包含InitSocState。”，它直接用于AI Core 全局状态初始化的 C++/C 两层入口。
- [asc_init（杂项接口）](../../../c_api/misc/asc_init.md)（`same_topic`）：《InitSocState》的任务是“初始化AI Core全局状态，包括AIC与AIV的公共状态及各自特有状态；不同产品实际执行的初始化项存在差异。”。《asc_init（杂项接口）》具体提供“本接口将当前AI Core上可能由前序算子遗留的全局状态恢复为接口约定的初始状态，避免这些状态影响当前算子的计算结果”，它直接用于AI Core 全局状态初始化的 C++/C 两层入口。
<!-- cannbot:related:end -->
