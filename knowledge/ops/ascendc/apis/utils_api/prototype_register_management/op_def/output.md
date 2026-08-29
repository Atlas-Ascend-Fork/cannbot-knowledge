---
type: API
title: Output（OpDef）
description: 注册算子输出，调用该接口后会返回一个OpParamDef结构，后续可通过该结构配置算子输出信息。
tags: [task.lookup, topic.implementation.api_layer.utils_api, topic.implementation.operator_registration]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/prototype_register_management/OpDef/Output.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# Output

## 功能说明
注册算子输出，调用该接口后会返回一个OpParamDef结构，后续可通过该结构配置算子输出信息。
## 函数原型
## 参数说明
## 返回值说明
算子参数定义，OpParamDef实例，具体请参考OpParamDef。
## 约束说明
参数注册的顺序需要和算子kernel入口函数一致。

<!-- cannbot:related:start -->
## 相关

- [advance_step in-place kernel FATBIN wrap](../../../../runbooks/compilation/fatbin_wrapper_param_count_matches_opdef_input_plus_output.md)（`exemplifies`）：ascend950 FATBIN 阶段为 kernel 自动生成一个 wrapper，wrapper 的调用实参数 = `OpDef` 声明的 input 数 + output 数 + workspace + tiling。；参数注册的顺序需要和算子kernel入口函数一致。；Output API 规定注册顺序与 Kernel 入口一致，排障实例进一步证明 wrapper 会按 input、output、workspace、tiling 机械生成实参，因此 Kernel 签名必须同时对齐 Output 数量和顺序。
<!-- cannbot:related:end -->
