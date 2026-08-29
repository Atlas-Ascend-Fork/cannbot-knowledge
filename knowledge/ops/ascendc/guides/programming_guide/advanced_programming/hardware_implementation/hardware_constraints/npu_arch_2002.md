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

- [GetCurNpuArch](../../../../../apis/utils_api/platform_info/platform_ascend_c/get_cur_npu_arch.md)（`explains`）：NPU架构版本2002不支持Generic Addressing通用寻址（针对UB、stack、GM等地址空间），因此语言层面地址空间必须匹配。；Atlas 推理系列产品AI Core：DAV_2002；GetCurNpuArch 的返回映射可在运行或 Host 选择阶段识别 DAV_2002，随后应用焦点卡的地址空间约束。
- [NPU架构版本2002](../architecture_spec/npu_arch_2002.md)（`same_topic`）：NPU架构版本2002不支持Generic Addressing通用寻址（针对UB、stack、GM等地址空间），因此语言层面地址空间必须匹配。；本节介绍__NPU_ARCH__版本号为2002的硬件架构和其功能说明。；两卡以同一 NPU_ARCH 2002 为核心对象，分别给出硬件组成与由其产生的地址空间编程约束。
<!-- cannbot:related:end -->
