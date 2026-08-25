---
type: Guide
title: NPU架构版本2002
description: 本节介绍硬件约束以及解决方案建议。对应的产品型号为：Atlas 推理系列产品。
tags: [task.lookup, topic.programming_model.execution_unit]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/programming_guide/advanced_programming/hardware_implementation/hardware_constraints/npu_arch_2002.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# NPU架构版本2002

本节介绍硬件约束以及解决方案建议。对应的产品型号为：Atlas 推理系列产品。
-   全局变量使用约束
NPU架构版本2002不支持Generic Addressing通用寻址（针对UB、stack、GM等地址空间），因此语言层面地址空间必须匹配。不同的地址空间信息不允许转换，不符合语法。全局变量位于GM上，传参位于stack上，函数内传参使用全局变量时会报错。目前编译器仅在优化级别为O0的场景下，对constexpr做了适配处理：将全局变量先从DDR上放到stack上。所以全局变量仅支持在O0下使用constexpr进行定义和使用，在其他场景均不支持。
-   支持场景
在O0下支持constexpr全局变量小规模类型（整型、浮点型）数据的引用，支持数组取元素。
-   不支持场景
对于使用constexpr之外的全局参数将报错。

<!-- cannbot:related:start -->
## 相关

- [GetCurNpuArch](../../../../../apis/utils_api/platform_info/platform_ascend_c/get_cur_npu_arch.md)（`explains`）：NPU架构版本2002 与《GetCurNpuArch》的实质衔接是：2002 architecture spec给出硬件组成，constraints给出 Generic Addressing/全局变量限制；GetCurNpuArch和 SoC 查证链用于确认当前目标确实落在2002。
- [Ascend arch 变体查证链路 SoC→ini→NpuArch→dispa](../../../../../runbooks/compilation/arch_variant_lookup_chain_soc_ini_npuarch_dispatcher.md)（`related`）：NPU架构版本2002 与《Ascend arch 变体查证链路 SoC→ini→NpuArch→dispa》的实质衔接是：2002 architecture spec给出硬件组成，constraints给出 Generic Addressing/全局变量限制；GetCurNpuArch和 SoC 查证链用于确认当前目标确实落在2002。
- [基本架构（硬件实现）](../basic_architecture.md)（`related`）：NPU架构版本2002 与《基本架构（硬件实现）》的实质衔接是：2002 architecture spec给出硬件组成，constraints给出 Generic Addressing/全局变量限制；GetCurNpuArch和 SoC 查证链用于确认当前目标确实落在2002。
- [NPU架构版本2002](../architecture_spec/npu_arch_2002.md)（`same_topic`）：NPU架构版本2002 与《NPU架构版本2002》的实质衔接是：2002 architecture spec给出硬件组成，constraints给出 Generic Addressing/全局变量限制；GetCurNpuArch和 SoC 查证链用于确认当前目标确实落在2002。
<!-- cannbot:related:end -->
