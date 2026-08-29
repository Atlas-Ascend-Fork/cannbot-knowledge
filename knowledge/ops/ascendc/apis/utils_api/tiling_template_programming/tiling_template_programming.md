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
