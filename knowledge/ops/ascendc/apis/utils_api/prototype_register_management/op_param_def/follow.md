---
type: API
title: Follow（OpParamDef）
description: 用于指定当前输入/输出的datatype/format/shape信息与之前定义过的某个输入一致。
tags: [task.lookup, topic.implementation.api_layer.utils_api, topic.implementation.operator_registration]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/prototype_register_management/OpParamDef/Follow.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# Follow

## 功能说明
用于指定当前输入/输出的datatype/format/shape信息与之前定义过的某个输入一致。
## 函数原型
-   datatype/format/shape全部信息保持一致
-   datatype/format/shape指定信息保持一致
## 参数说明
## 返回值说明
OpParamDef算子定义，OpParamDef请参考OpParamDef。
## 约束说明
-   所有Follow的数据源头仅支持为Input。
-   针对shape推导，仅支持输出参数Follow输入参数，不支持输入参数Follow另一个输入参数。
-   可以支持链式Follow，例如C Follow B，B Follow A，但此时Follow的模式不可中途变更（ftype需要保持一致）。
-   使用Follow接口通常比InferShape函数逻辑更加简单，能用Follow表达的逻辑，建议使用Follow接口，则无需再编写注册InferShape函数。
-   InferShape推导函数和使用Follow接口去Follow shape不能混用，即不支持部分输出采用Infershape推导、部分输出采用Follow推导的情况。若用户同时使用了InferShape函数和Follow接口，以用户的InferShape函数为准，需要保证在InferShape函数中能够推导出所有的输出shape。
-   datatype/format同时支持Follow输入的参数类型为DataTypeList/FormatList，调用Follow后，当前输入/输出的datatype/format与paramName组合后的datatype/format一致。

<!-- cannbot:related:start -->
## 相关

- [optional input 未连接触发 InferShape 失败](../../../../runbooks/compilation/optional_input_infershape.md)（`exemplifies`）：《optional input 未连接触发 InferShape 失败》处理“OpDef 声明含 optional input、GEIR 图未连接该 input 时，本例在 ConstructInferShapeContextInputs 阶段 assert；用于确认失败发生在算子 InferShape 回调之前，并核对声明输入与实际连边。”。《Follow（OpParamDef）》明确提供“用于指定当前输入/输出的datatype/format/shape信息与之前定义过的某个输入一致。”，其参数、调用或验证步骤直接接入可选输入在 OpDef/原型/InferShape/InferShapeRange 中的上下文合同。
- [基本开发流程](../../../../guides/programming_guide/advanced_programming/operator_graph_development/basic_development_flow.md)（`explains`）：基本开发流程 与《Follow（OpParamDef）》的实质衔接是：算子图基本流程把 OpDef 原型、InferShape/InferDataType、图编译执行和 tiling 下沉串成同一生命周期；三个失败案例分别验证原型加载、可选输入和 shape 推导不能被绕过。
- [DataType（OpParamDef）](data_type.md)（`related`）：Follow 复用另一参数的 dtype/format/shape，而 DataType 显式列出允许 dtype。
- [Format（OpParamDef）](format.md)（`related`）：Follow 同时可传播 format/shape 约束。
- [Scalar（OpParamDef）](scalar.md)（`related`）：《Follow（OpParamDef）》明确“用于指定当前输入/输出的datatype/format/shape信息与之前定义过的某个输入一致。”；它与《Scalar（OpParamDef）》的“配置该参数后，自动生成的单算子API（aclnnxxx）接口中，输入类型为aclScalar类型。”在实际调用参数、数据流或结果校验上直接衔接。
- [Input（OpDef）](../op_def/input.md)（`same_topic`）：焦点处理OpDef Input 的参数类型、格式、可选性和值依赖配置；Follow（OpParamDef）正文说明“用于指定当前输入/输出的datatype/format/shape信息与之前定义过的某个输入一致”。候选配置 Input 返回的 OpParamDef，或复现输入可选性、格式和值依赖造成的框架故障。
- [Input（原型注册管理）](../op_ai_core_config/input.md)（`same_topic`）：《Input（原型注册管理）》处理“某些场景下，同一个算子在不同的AI处理器型号上，其支持的原型输入不同。 通过该接口，可针对不同的AI处理器型号注册差异化的算子原型。调用该接口后会返回一个OpParamDef结构，后续可通过该结构配置算子输入信息。”。《Follow（OpParamDef）》明确“用于指定当前输入/输出的datatype/format/shape信息与之前定义过的某个输入一致。”，可直接用于核对算子 Input/Output 原型、OpParamDef dtype/format/optional/value-depend 参数及已证注册故障。
- [OpParamDef](op_param_def.md)（`same_topic`）：Follow 是 OpParamDef 的链式配置。
<!-- cannbot:related:end -->
