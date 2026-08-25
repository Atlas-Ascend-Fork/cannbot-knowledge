---
type: API
title: Format（OpParamDef）
description: 定义算子参数数据格式。
tags: [task.lookup, topic.implementation.api_layer.utils_api, topic.implementation.operator_registration]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/prototype_register_management/OpParamDef/Format.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# Format

## 功能说明
定义算子参数数据格式。
## 函数原型
## 参数说明
## 返回值说明
OpParamDef算子定义，OpParamDef请参考OpParamDef。
## 约束说明
无

<!-- cannbot:related:start -->
## 相关

- [Follow（OpParamDef）](follow.md)（`related`）：Follow 同时可传播 format/shape 约束。
- [FormatForBinQuery](format_for_bin_query.md)（`related`）：FormatForBinQuery 在二进制查询阶段补充该参数的格式匹配信息，与 Format 的运行原型格式共同决定选包条件。
- [FormatList](format_list.md)（`same_topic`）：FormatList 的核心契约是“定义算子参数数据格式，当某个输入/输出的格式可与其他所有输入/输出的数据类型和格式自由组合时使用，无需重复列出所有组合”；Format（OpParamDef） 补充“定义算子参数数据格式”。
- [Input（OpDef）](../op_def/input.md)（`same_topic`）：焦点处理OpDef Input 的参数类型、格式、可选性和值依赖配置；Format（OpParamDef）正文说明“定义算子参数数据格式”。候选配置 Input 返回的 OpParamDef，或复现输入可选性、格式和值依赖造成的框架故障。
- [Input（原型注册管理）](../op_ai_core_config/input.md)（`same_topic`）：《Input（原型注册管理）》处理“某些场景下，同一个算子在不同的AI处理器型号上，其支持的原型输入不同。 通过该接口，可针对不同的AI处理器型号注册差异化的算子原型。调用该接口后会返回一个OpParamDef结构，后续可通过该结构配置算子输入信息。”。《Format（OpParamDef）》明确“定义算子参数数据格式。”，可直接用于核对算子 Input/Output 原型、OpParamDef dtype/format/optional/value-depend 参数及已证注册故障。
- [UnknownShapeFormat](unknown_shape_format_deprecated.md)（`same_topic`）：《Format（OpParamDef）》明确“定义算子参数数据格式。”；它与《UnknownShapeFormat》的“已废弃接口，设置未知Shape情况下的Format默认值，请统一使用Format接口替代。”在实际调用参数、数据流或结果校验上直接衔接。
<!-- cannbot:related:end -->
