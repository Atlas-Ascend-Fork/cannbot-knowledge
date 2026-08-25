---
type: API
title: 构造&拷贝构造函数（OpParamDef）
description: 构造算子参数的OpParamDef，OpParamDef用于描述算子参数的信息，如数据类型、格式等。一般用户不会直接构造OpParamDef，而是通过Input、Output接口间接构造算子参数的OpParamDef。
tags: [task.lookup, topic.implementation.api_layer.utils_api, topic.implementation.operator_registration]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/prototype_register_management/OpParamDef/constructor_and_copy_constructor.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# 构造&拷贝构造函数

## 功能说明
构造算子参数的OpParamDef，OpParamDef用于描述算子参数的信息，如数据类型、格式等。一般用户不会直接构造OpParamDef，而是通过Input、Output接口间接构造算子参数的OpParamDef。
## 函数原型
## 参数说明
## 返回值说明
无
## 约束说明
无

<!-- cannbot:related:start -->
## 相关

- [Output（OpDef）](../op_def/output.md)（`related`）：OpDef::Output 注册输出并返回 OpParamDef，提供 focal 所述的另一合法构造路径，后续再配置输出属性。
- [Comment](comment.md)（`same_topic`）：Comment 与《构造&拷贝构造函数（OpParamDef）》的实质衔接是：Comment 写入 OpParamDef 的 input/output 注释并传播到自动生成原型和文档；构造、Input/Output、OpDef 与另一注册层 Comment 是同一元数据链。
- [DataTypeForBinQuery](data_type_for_bin_query.md)（`same_topic`）：DataTypeForBinQuery 与《构造&拷贝构造函数（OpParamDef）》的实质衔接是：DataTypeForBinQuery 与 FormatForBinQuery 共同决定运行时二进制键；OpParamDef 的类型/格式列表、Version、Input 及 InferDataType 必须保持注册与推导一致。
- [Input（OpDef）](../op_def/input.md)（`same_topic`）：焦点处理OpDef Input 的参数类型、格式、可选性和值依赖配置；构造&拷贝构造函数（OpParamDef）正文说明“构造算子参数的OpParamDef，OpParamDef用于描述算子参数的信息，如数据类型、格式等。一般用户不会直接构造OpParamDef，而是通过Input、Output接口间接构造算子参数的OpParamDef”。候选配置 Input 返回的 OpParamDef，或复现输入可选性、格式和值依赖造成的框架故障。
- [Input（原型注册管理）](../op_ai_core_config/input.md)（`same_topic`）：《Input（原型注册管理）》处理“某些场景下，同一个算子在不同的AI处理器型号上，其支持的原型输入不同。 通过该接口，可针对不同的AI处理器型号注册差异化的算子原型。调用该接口后会返回一个OpParamDef结构，后续可通过该结构配置算子输入信息。”。《构造&拷贝构造函数（OpParamDef）》明确“构造算子参数的OpParamDef，OpParamDef用于描述算子参数的信息，如数据类型、格式等。一般用户不会直接构造OpParamDef，而是通过Input、Output接口间接构造算子参数的OpParamDef。”，可直接用于核对算子 Input/Output 原型、OpParamDef dtype/format/optional/value-depend 参数及已证注册故障。
- [Scalar（OpParamDef）](scalar.md)（`same_topic`）：《构造&拷贝构造函数（OpParamDef）》明确“构造算子参数的OpParamDef，OpParamDef用于描述算子参数的信息，如数据类型、格式等。一般用户不会直接构造OpParamDef，而是通过Input、Output接口间接构造算子参数的OpParamDef。”；它与《Scalar（OpParamDef）》的“配置该参数后，自动生成的单算子API（aclnnxxx）接口中，输入类型为aclScalar类型。”在实际调用参数、数据流或结果校验上直接衔接。
<!-- cannbot:related:end -->
