---
type: API
title: Tiling模板编程
description: Tiling模板编程接口索引。
tags: [task.lookup, topic.programming_model]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/Tiling_template_programming/Tiling_template_programming.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---
# Tiling模板编程

Tiling模板编程接口集合，通过C++模板机制实现多分支Tiling策略的编译期选择和代码生成。包含模板参数定义（template_params_definition，用于配置Tiling模板的编译期参数）、GET_TPL_TILING_KEY（获取模板Tiling Key，用于区分不同Tiling策略版本）、ASCENDC_TPL_SEL_PARAM（模板选择参数宏，用于在编译期选择不同的Tiling实现分支）。模板编程可减少运行时分支判断开销。

<!-- cannbot:related:start -->
## 相关

- [AscendC 标量类型误加命名空间导致模板分发编译失败](../../../runbooks/compilation/device_half_bfloat16_types_are_global.md)（`exemplifies`）：Tiling模板编程 与《AscendC 标量类型误加命名空间导致模板分发编译失败》的实质衔接是：Tiling 模板编程依赖参数声明、选择宏和 key 获取；所选编译故障直接约束模板类型与分发实例化。
- [GET_TILING_DATA_WITH_STRUCT 宏不接受模板类型](../../../runbooks/compilation/get_tiling_data_with_struct.md)（`exemplifies`）：Tiling模板编程 与《GET_TILING_DATA_WITH_STRUCT 宏不接受模板类型》的实质衔接是：Tiling 模板编程依赖参数声明、选择宏和 key 获取；所选编译故障直接约束模板类型与分发实例化。
- [模板内 float→float Cast 使 fp32 分支全错](../../../runbooks/precision/templated_float_input_must_bypass_same_type_cast.md)（`exemplifies`）：Tiling模板编程 与《模板内 float→float Cast 使 fp32 分支全错》的实质衔接是：Tiling 模板编程依赖参数声明、选择宏和 key 获取；所选编译故障直接约束模板类型与分发实例化。
- [ASCENDC_TPL_SEL_PARAM](ascendc_tpl_sel_param.md)（`same_topic`）：ASCENDC_TPL_SEL_PARAM 与《Tiling模板编程》的实质衔接是：TPL 参数必须与模板定义、GET_TPL_TILING_KEY 和 TILING_KEY_IS 位编码一致；所选故障卡覆盖缺宏、头文件、funcEntry 和缓存复用失配。
- [GET_TPL_TILING_KEY](get_tpl_tiling_key.md)（`same_topic`）：Tiling模板编程 与《GET_TPL_TILING_KEY》的实质衔接是：Tiling 模板编程依赖参数声明、选择宏和 key 获取；所选编译故障直接约束模板类型与分发实例化。
- [模板参数定义](template_params_definition.md)（`same_topic`）：Tiling模板编程 与《模板参数定义》的实质衔接是：Tiling 模板编程依赖参数声明、选择宏和 key 获取；所选编译故障直接约束模板类型与分发实例化。
<!-- cannbot:related:end -->
