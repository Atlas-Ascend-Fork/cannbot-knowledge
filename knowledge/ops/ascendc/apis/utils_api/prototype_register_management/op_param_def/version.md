---
type: API
title: Version
description: 为可选输入配置aclnn接口版本号，版本号从1开始连续配置，高版本接口包含低版本所有参数，保持向后兼容。
tags: [task.lookup, topic.implementation.api_layer.utils_api, topic.implementation.operator_registration]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/prototype_register_management/OpParamDef/Version.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# Version

## 功能说明
算子编译部署后，会自动生成单算子API(aclnnxxx)接口，接口中的输入输出参数和算子原型定义中保持一致。
新增可选输入时，为了保持原有单算子API(aclnnxxx)接口的兼容性，可以通过Version接口配置aclnn接口的版本号，版本号需要从1开始配，且应该连续配置（和可选属性统一编号）。配置后，自动生成的aclnn接口会携带版本号。高版本号的接口会包含低版本号接口的所有参数。如下样例所示的原型定义：
会自动生成3个版本的aclnn接口，定义如下：
## 函数原型
## 参数说明
## 返回值说明
OpParamDef算子定义，OpParamDef请参考OpParamDef。
## 约束说明
无

<!-- cannbot:related:start -->
## 相关

- [ParamType（OpParamDef）](param_type.md)（`related`）：ParamType marks an input optional; Version then assigns consecutive aclnn interface versions when such optional inputs are introduced.
- [DataTypeForBinQuery](data_type_for_bin_query.md)（`same_topic`）：DataTypeForBinQuery 与《Version》的实质衔接是：DataTypeForBinQuery 与 FormatForBinQuery 共同决定运行时二进制键；OpParamDef 的类型/格式列表、Version、Input 及 InferDataType 必须保持注册与推导一致。
- [OpAttrDef](../op_attr_def/op_attr_def.md)（`same_topic`）：OpAttrDef 与《Version》的实质衔接是：OpAttrDef 定义属性名、类型、OPTIONAL/REQUIRED、默认值和 Version；Comment 生成原型注释，OpDef::Attr 挂载属性，Host TilingData 传递与缓存故障说明 runtime 属性进入 kernel 时的后续契约。
<!-- cannbot:related:end -->
