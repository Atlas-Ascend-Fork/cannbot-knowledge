---
type: API
title: AutoContiguous
description: 配置该参数，当单算子API（aclnnxxx）接口中的输入（aclTensor类型）是非连续tensor时，框架会自动将其转换为连续tensor。
  该接口仅在如下场景支持： - 通过单算子API执行的方式开发单算子调用应用。 - 间接调用单算子API\(aclnnxxx\)接口：Pytorch框架单算子直调的场景。
tags: [task.lookup, topic.implementation.api_layer.utils_api, topic.implementation.operator_registration]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/prototype_register_management/OpParamDef/AutoContiguous.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# AutoContiguous

## 功能说明
配置该参数，当单算子API（aclnnxxx）接口中的输入（aclTensor类型）是非连续tensor时，框架会自动将其转换为连续tensor。
该接口仅在如下场景支持：
-   通过单算子API执行的方式开发单算子调用应用。
-   间接调用单算子API(aclnnxxx)接口：Pytorch框架单算子直调的场景。
## 函数原型
## 参数说明
无
## 返回值说明
OpParamDef算子定义，OpParamDef请参考OpParamDef。
## 约束说明
当一个Input调用了AutoContigous()后，其他未调用IgnoreContiguous()的Input也会在框架中默认进行非连续tensor转连续tensor的处理。

<!-- cannbot:related:start -->
## 相关

- [ACLNN 561000 非连续张量需 AutoContiguous](../../../../runbooks/compilation/aclnn_561000_autocontiguous.md)（`exemplifies`）：在 `Input("self")` 的 `OpParamDef` 链尾追加 `.AutoContiguous()` 后，非连续 view（transpose/slice）用例 ST 通过；配置该参数，当单算子API（aclnnxxx）接口中的输入（aclTensor类型）是非连续tensor时，框架会自动将其转换为连续tensor。。运行手册用真实 transpose 和 slice 用例验证在 Input 定义追加 AutoContiguous 可修复非连续输入，API 卡解释其自动转换为连续 tensor 的框架行为，是规则在故障修复中的直接实例。
<!-- cannbot:related:end -->
