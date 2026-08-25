---
type: API
title: DataTypeList
description: 定义算子参数数据类型，当某个输入/输出的数据类型可与其他所有输入/输出的数据类型和格式自由组合时使用，无需重复列出所有组合。
tags: [task.lookup, topic.implementation.api_layer.utils_api, topic.implementation.operator_registration]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/prototype_register_management/OpParamDef/DataTypeList.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# DataTypeList

## 功能说明
定义算子参数数据类型。如果某个输入/输出支持的数据类型支持和其他所有输入/输出支持的数据类型、数据格式组合使用，可以使用该接口定义数据类型。
使用DataType配置数据类型时，算子参数的数据类型和格式必须通过显式组合配置，每个组合包含完整的输入/输出数据类型与数据格式的对应关系。如下的示例中表示：当输入x和y数据类型为DT_FLOAT16时，对应的输出z数据类型也为DT_FLOAT16，支持的数据格式要求为FORMAT_ND。
如果某个输入/输出支持的数据类型支持和其他所有输入/输出支持的数据类型、数据格式组合使用，使用DataType接口需要写成如下的格式，表示当输入x为DT_FLOAT16时，支持输入y和输入z的所有数据类型、数据格式组合。
此时可以通过DataTypeList指定数据类型，无需重复列出，例如：
## 函数原型
## 参数说明
## 返回值说明
OpParamDef算子定义，OpParamDef请参考OpParamDef。
## 约束说明
-   同一输入/输出不能同时设置DataType和DataTypeList。
-   本接口不支持和UnknownShapeFormat同时使用。

<!-- cannbot:related:start -->
## 相关

- [DataTypeForBinQuery](data_type_for_bin_query.md)（`same_topic`）：DataTypeForBinQuery 与《DataTypeList》的实质衔接是：DataTypeForBinQuery 与 FormatForBinQuery 共同决定运行时二进制键；OpParamDef 的类型/格式列表、Version、Input 及 InferDataType 必须保持注册与推导一致。
- [DataType（OpParamDef）](data_type.md)（`same_topic`）：DataType 要求显式列出输入输出 dtype/format 组合，DataTypeList 用于某参数可与其余组合自由笛卡尔组合时去重；二者的选择决定原型组合表达。
<!-- cannbot:related:end -->
