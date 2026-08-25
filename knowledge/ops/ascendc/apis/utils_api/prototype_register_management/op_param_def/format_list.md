---
type: API
title: FormatList
description: 定义算子参数数据格式，当某个输入/输出的格式可与其他所有输入/输出的数据类型和格式自由组合时使用，无需重复列出所有组合。
tags: [task.lookup, topic.implementation.api_layer.utils_api, topic.implementation.operator_registration]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/prototype_register_management/OpParamDef/FormatList.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# FormatList

## 功能说明
定义算子参数数据格式。如果某个输入/输出支持的数据格式支持和其他所有输入/输出支持的数据类型、数据格式组合使用，可以使用该接口定义数据格式。
使用Format配置数据格式时，这些数据格式和其他输入输出的数据类型和数据格式是一一对应的，如下的示例中表示：当输入x和y数据格式为FORMAT_NHWC时，对应的输出z数据格式也为FORMAT_NHWC，且此时x、y、z的数据类型要求为ge::DT_FLOAT。
如果某个输入/输出支持的数据格式支持和其他所有输入/输出支持的数据类型、数据格式组合使用，使用Format接口需要写成如下的格式，表示当输入x为FORMAT_ND时，支持输入y和输入z的所有数据类型、数据格式组合。
此时可以通过FormatList指定数据类型，无需重复列出，例如：
## 函数原型
## 参数说明
## 返回值说明
OpParamDef算子定义，OpParamDef请参考OpParamDef。
## 约束说明
-   同一输入/输出不能同时设置Format和FormatList。
-   本接口不支持和UnknownShapeFormat同时使用。

<!-- cannbot:related:start -->
## 相关

- [FormatForBinQuery](format_for_bin_query.md)（`related`）：参数使用 FormatList 自由组合格式时，FormatForBinQuery 仍须保持相同个数和位置；FormatList 还不能与同一参数的 Format 并用。
- [DataTypeForBinQuery](data_type_for_bin_query.md)（`same_topic`）：DataTypeForBinQuery 与《FormatList》的实质衔接是：DataTypeForBinQuery 与 FormatForBinQuery 共同决定运行时二进制键；OpParamDef 的类型/格式列表、Version、Input 及 InferDataType 必须保持注册与推导一致。
- [Format（OpParamDef）](format.md)（`same_topic`）：FormatList 的核心契约是“定义算子参数数据格式，当某个输入/输出的格式可与其他所有输入/输出的数据类型和格式自由组合时使用，无需重复列出所有组合”；Format（OpParamDef） 补充“定义算子参数数据格式”。
<!-- cannbot:related:end -->
