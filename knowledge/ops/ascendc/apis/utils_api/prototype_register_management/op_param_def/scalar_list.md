---
type: API
title: ScalarList
description: 配置该参数后，自动生成的单算子API（aclnnxxx）接口中，输入类型为aclScalarList类型。
tags: [task.lookup, topic.implementation.api_layer.utils_api, topic.implementation.operator_registration]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/prototype_register_management/OpParamDef/ScalarList.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# ScalarList

## 功能说明
配置该参数后，自动生成的单算子API（aclnnxxx）接口中，输入类型为aclScalarList类型。
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

- [ForeachPowScalarList A2/A3 ACLNN 算子知识](../../../../operators/aclnn/nn/foreach/foreach_pow_scalar_list.md)（`related`）：ForeachPowScalarList 的 ABI 写明“`scalars` 为与列表等长的 `FLOAT32/INT64` ScalarList”；ScalarList 页定义“配置该参数后，自动生成的单算子API（aclnnxxx）接口中，输入类型为aclScalarList类型。”，后者解释 ACLNN bridge 如何暴露前者指数列表输入。
<!-- cannbot:related:end -->
