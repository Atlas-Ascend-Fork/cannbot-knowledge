---
type: API
title: DataTypeForBinQuery
description: 设置Input/Output用于运行时算子二进制查找的数据类型，将多种数据类型映射到同一个算子二进制，减少二进制文件生成数量。
tags: [task.lookup, topic.implementation.api_layer.utils_api, topic.implementation.operator_registration]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/prototype_register_management/OpParamDef/DataTypeForBinQuery.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# DataTypeForBinQuery

## 功能说明
设置Input/Output用于运行时算子二进制查找的数据类型，和DataType/DataTypeList的数量一致，且一一对应。
算子编译过程中，会根据数据类型生成多个.o，并通过这些数据类型在运行时索引算子二进制。某些算子支持多种数据类型，且对数据类型不敏感，这时可以使用该接口，将多种数据类型映射到同一个算子二进制，多个数据类型可以复用一个.o，从而减少二进制文件的生成。
例如，如果一个算子的输入支持多种数据类型（ge::DT_INT16和ge::DT_INT32），并且使用ge::DT_INT16输入时可以复用ge::DT_INT32 的二进制文件而不影响最终结果，那么可以采用如下配置：
这样，只需生成一个目标文件（.o），就能实现对多种数据类型的支持。
## 函数原型
## 参数说明
## 返回值说明
OpParamDef算子定义，OpParamDef请参考OpParamDef。
## 约束说明
-   DataTypeForBinQuery的参数个数需要和当前算子参数的DataType或者DataTypeList的参数个数保持一致。
-   不支持与To（指定数据类型）的接口同时使用。
-   需要保证使用DataTypeForBinQuery后，产生新的算子参数属性集合（使用DataTypeForBinQuery替换原本DataType序列）存在于原本支持的参数属性集合中。
参数属性集合的定义为，算子所支持的所有参数的属性的集合，相当于一列参数的集合。
例如示例一中。算子支持四种原集合，没有重复。
1、x : DT_FLOAT16, FORMAT_ND    y : DT_INT16, FORMAT_ND
2、x : DT_FLOAT, FORMAT_ND    y : DT_INT16, FORMAT_ND
3、x : DT_INT16, FORMAT_ND    y : DT_INT16, FORMAT_ND
4、x : DT_INT32, FORMAT_ND    y : DT_INT16, FORMAT_NC
使用DataTypeForBinQuery替换原本DataType序列后，新集合为
1、x : DT_INT16, FORMAT_ND    y : DT_INT16, FORMAT_ND
2、x : DT_FLOAT16, FORMAT_ND    y : DT_INT16, FORMAT_ND
3、x : DT_FLOAT16, FORMAT_ND    y : DT_INT16, FORMAT_ND
4、x : DT_INT16, FORMAT_ND    y : DT_INT16, FORMAT_NC
此时发现，新集合1与原集合3一致，新集合2、新集合3与原集合1一致。设置生效。新集合4不属于原集合，设置失效。此时会按照原本的集合4进行编译。

<!-- cannbot:related:start -->
## 相关

- [算子原型定义](../../../../guides/programming_guide/advanced_programming/aclnn_operator_development/design_and_implementation/operator_prototype_definition.md)（`explains`）：DataTypeForBinQuery 与《算子原型定义》的实质衔接是：DataTypeForBinQuery 与 FormatForBinQuery 共同决定运行时二进制键；OpParamDef 的类型/格式列表、Version、Input 及 InferDataType 必须保持注册与推导一致。
- [DataTypeList](data_type_list.md)（`same_topic`）：DataTypeForBinQuery 与《DataTypeList》的实质衔接是：DataTypeForBinQuery 与 FormatForBinQuery 共同决定运行时二进制键；OpParamDef 的类型/格式列表、Version、Input 及 InferDataType 必须保持注册与推导一致。
- [DataType（OpParamDef）](data_type.md)（`same_topic`）：DataTypeForBinQuery 与《DataType（OpParamDef）》的实质衔接是：DataTypeForBinQuery 与 FormatForBinQuery 共同决定运行时二进制键；OpParamDef 的类型/格式列表、Version、Input 及 InferDataType 必须保持注册与推导一致。
- [FormatForBinQuery](format_for_bin_query.md)（`same_topic`）：DataTypeForBinQuery 与《FormatForBinQuery》的实质衔接是：DataTypeForBinQuery 与 FormatForBinQuery 共同决定运行时二进制键；OpParamDef 的类型/格式列表、Version、Input 及 InferDataType 必须保持注册与推导一致。
- [FormatList](format_list.md)（`same_topic`）：DataTypeForBinQuery 与《FormatList》的实质衔接是：DataTypeForBinQuery 与 FormatForBinQuery 共同决定运行时二进制键；OpParamDef 的类型/格式列表、Version、Input 及 InferDataType 必须保持注册与推导一致。
- [Input（OpDef）](../op_def/input.md)（`same_topic`）：DataTypeForBinQuery 与《Input（OpDef）》的实质衔接是：DataTypeForBinQuery 与 FormatForBinQuery 共同决定运行时二进制键；OpParamDef 的类型/格式列表、Version、Input 及 InferDataType 必须保持注册与推导一致。
- [Input（原型注册管理）](../op_ai_core_config/input.md)（`same_topic`）：DataTypeForBinQuery 与《Input（原型注册管理）》的实质衔接是：DataTypeForBinQuery 与 FormatForBinQuery 共同决定运行时二进制键；OpParamDef 的类型/格式列表、Version、Input 及 InferDataType 必须保持注册与推导一致。
- [OpParamDef](op_param_def.md)（`same_topic`）：DataTypeForBinQuery 与《OpParamDef》的实质衔接是：DataTypeForBinQuery 与 FormatForBinQuery 共同决定运行时二进制键；OpParamDef 的类型/格式列表、Version、Input 及 InferDataType 必须保持注册与推导一致。
- [SetInferDataType](../op_def/set_infer_data_type.md)（`same_topic`）：DataTypeForBinQuery 与《SetInferDataType》的实质衔接是：DataTypeForBinQuery 与 FormatForBinQuery 共同决定运行时二进制键；OpParamDef 的类型/格式列表、Version、Input 及 InferDataType 必须保持注册与推导一致。
- [TensorDataType](../../../simd_api/adv_api/data_structures/tensor_data_type.md)（`same_topic`）：DataTypeForBinQuery 与《TensorDataType》的实质衔接是：DataTypeForBinQuery 与 FormatForBinQuery 共同决定运行时二进制键；OpParamDef 的类型/格式列表、Version、Input 及 InferDataType 必须保持注册与推导一致。
- [Version](version.md)（`same_topic`）：DataTypeForBinQuery 与《Version》的实质衔接是：DataTypeForBinQuery 与 FormatForBinQuery 共同决定运行时二进制键；OpParamDef 的类型/格式列表、Version、Input 及 InferDataType 必须保持注册与推导一致。
- [构造&拷贝构造函数（OpParamDef）](constructor_and_copy_constructor.md)（`same_topic`）：DataTypeForBinQuery 与《构造&拷贝构造函数（OpParamDef）》的实质衔接是：DataTypeForBinQuery 与 FormatForBinQuery 共同决定运行时二进制键；OpParamDef 的类型/格式列表、Version、Input 及 InferDataType 必须保持注册与推导一致。
<!-- cannbot:related:end -->
