---
type: API
title: Scalar（OpParamDef）
description: 配置该参数后，自动生成的单算子API（aclnnxxx）接口中，输入类型为aclScalar类型。
tags: [task.lookup, topic.implementation.api_layer.utils_api, topic.implementation.operator_registration]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/prototype_register_management/OpParamDef/Scalar.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# Scalar

## 功能说明
配置该参数后，自动生成的单算子API（aclnnxxx）接口中，输入类型为aclScalar类型。
## 函数原型
## 参数说明
无
## 返回值说明
OpParamDef算子定义，OpParamDef请参考OpParamDef。
## 约束说明
-   仅支持对算子输入做该参数配置，如果对算子输出配置该参数，则配置无效。
-   该接口仅在如下场景支持：
-   通过单算子API执行的方式开发单算子调用应用。
-   间接调用单算子API(aclnnxxx)接口：Pytorch框架单算子直调的场景。

<!-- cannbot:related:start -->
## 相关

- [DataType（OpParamDef）](data_type.md)（`related`）：《DataType（OpParamDef）》明确“定义算子参数数据类型。”；它与《Scalar（OpParamDef）》的“配置该参数后，自动生成的单算子API（aclnnxxx）接口中，输入类型为aclScalar类型。”在实际调用参数、数据流或结果校验上直接衔接。
- [Follow（OpParamDef）](follow.md)（`related`）：《Follow（OpParamDef）》明确“用于指定当前输入/输出的datatype/format/shape信息与之前定义过的某个输入一致。”；它与《Scalar（OpParamDef）》的“配置该参数后，自动生成的单算子API（aclnnxxx）接口中，输入类型为aclScalar类型。”在实际调用参数、数据流或结果校验上直接衔接。
- [To](to.md)（`related`）：To binds a declared OpParamDef Scalar to its runtime scalar value, completing the parameter-definition contract.
- [Input（OpDef）](../op_def/input.md)（`same_topic`）：焦点处理OpDef Input 的参数类型、格式、可选性和值依赖配置；Scalar（OpParamDef）正文说明“配置该参数后，自动生成的单算子API（aclnnxxx）接口中，输入类型为aclScalar类型”。候选配置 Input 返回的 OpParamDef，或复现输入可选性、格式和值依赖造成的框架故障。
- [Input（原型注册管理）](../op_ai_core_config/input.md)（`same_topic`）：《Input（原型注册管理）》处理“某些场景下，同一个算子在不同的AI处理器型号上，其支持的原型输入不同。 通过该接口，可针对不同的AI处理器型号注册差异化的算子原型。调用该接口后会返回一个OpParamDef结构，后续可通过该结构配置算子输入信息。”。《Scalar（OpParamDef）》明确“配置该参数后，自动生成的单算子API（aclnnxxx）接口中，输入类型为aclScalar类型。”，可直接用于核对算子 Input/Output 原型、OpParamDef dtype/format/optional/value-depend 参数及已证注册故障。
- [构造&拷贝构造函数（OpParamDef）](constructor_and_copy_constructor.md)（`same_topic`）：《构造&拷贝构造函数（OpParamDef）》明确“构造算子参数的OpParamDef，OpParamDef用于描述算子参数的信息，如数据类型、格式等。一般用户不会直接构造OpParamDef，而是通过Input、Output接口间接构造算子参数的OpParamDef。”；它与《Scalar（OpParamDef）》的“配置该参数后，自动生成的单算子API（aclnnxxx）接口中，输入类型为aclScalar类型。”在实际调用参数、数据流或结果校验上直接衔接。
<!-- cannbot:related:end -->
