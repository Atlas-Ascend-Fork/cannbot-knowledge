---
type: API
title: ASCENDC_TPL_SEL_PARAM
description: Tiling模板编程时，开发者通过调用此接口自动生成并配置TilingKey。 使用该接口需要包含定义模板参数和模板参数组合的头文件。详细内容请参考Tiling模板编程。
tags: [task.lookup, topic.implementation.api_layer.utils_api]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/Tiling_template_programming/ASCENDC_TPL_SEL_PARAM.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# ASCENDC_TPL_SEL_PARAM

Tiling 模板编程时，开发者通过调用此宏自动生成并配置 TilingKey。使用前需包含定义模板参数和模板参数组合的头文件。
宏展开后调用 GET_TPL_TILING_KEY 计算模板参数对应的 key 值，再通过 context->SetTilingKey 设置。
参数 context 为 TilingFunc 注册上下文（gert::TilingContext*），可变参数为模板参数具体值，需与头文件中模板参数顺序一致。
无返回值，无特殊约束。
典型用法：在 TilingFunc 中根据数据类型、切分策略等条件确定模板参数值，调用 ASCENDC_TPL_SEL_PARAM(context, D_T_X, D_T_Y, D_T_Z, TILE_NUM, IS_SPLIT) 自动设置 TilingKey。
