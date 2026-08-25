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

- [ACLNN 561000 非连续张量需 AutoContiguous](../../../../runbooks/compilation/aclnn_561000_autocontiguous.md)（`exemplifies`）：ACLNN 561000 非连续张量需 AutoContiguous 与《AutoContiguous》的实质衔接是：561000 来自 OpParamDef 未声明连续性策略；AutoContiguous/IgnoreContiguous、Input/OpDef 和非连续 Load/Store/Slice/Transpose 卡共同决定转换还是保留 strides。
- [MulPreferContiguous 稀疏广播拦截失败且慢于 304](../../../../runbooks/performance/mulprefercontiguous_304.md)（`exemplifies`）：《MulPreferContiguous 稀疏广播拦截失败且慢于 304》处理“B 类稀疏广播（首轴稀疏、stride 大）触发 MulPreferContiguous 拦截转连续，baseline GetWorkspaceSize 返回 -1.0（schMode 空）或性能慢于 fixed 直接走 304 nddma_transpose_noLoop。”。《AutoContiguous》提供“配置该参数，当单算子API（aclnnxxx）接口中的输入（aclTensor类型）是非连续tensor时，框架会自动将其转换为连续tensor。 该接口仅在如下场景支持： - 通过单算子API执行的方式开发单算子调用应用。 - 间接调用单算子API\(aclnnxxx\)接口：Pytorch框架单算子直调的场景。”，其具体合同或探针直接接入稀疏广播输入的 contiguous 拦截、304 路由和非连续 shape/stride 合同。
- [批次行索引未对 M 回绕致整行置零判别](../../../../runbooks/precision/m.md)（`exemplifies`）：《批次行索引未对 M 回绕致整行置零判别》处理“批次化逐元素掩码 kernel 用线性偏移 gmOffset % (M*N) 反推 (i,j)，在 chunk 循环内推进行索引时 i += newJ/N 未对 M 取模；tile 跨 batch 边界时 batch>0 的行 0 得到 i=M 而非 i=0，使 start_col=clamp(i+diagonal,0,N)=N、keep 区间为空、整行误置零。判别=只在 rank≥3 且 batch>1 的用例失败、且表现为整行置零而非逐元素错位。”。《AutoContiguous》提供“配置该参数，当单算子API（aclnnxxx）接口中的输入（aclTensor类型）是非连续tensor时，框架会自动将其转换为连续tensor。 该接口仅在如下场景支持： - 通过单算子API执行的方式开发单算子调用应用。 - 间接调用单算子API\(aclnnxxx\)接口：Pytorch框架单算子直调的场景。”，其具体合同或探针直接接入批次 tile 跨 M 边界的行索引回绕、AutoContiguous 排除和 rank≥3 验证。
- [IgnoreContiguous](ignore_contiguous.md)（`related`）：IgnoreContiguous 与《AutoContiguous》的实质衔接是：IgnoreContiguous 与 AutoContiguous 是非连续 aclTensor 的两种 OpParamDef 策略，561000 故障给出缺失配置时的可复现实例。
- [Input（原型注册管理）](../op_ai_core_config/input.md)（`related`）：《Input（原型注册管理）》处理“某些场景下，同一个算子在不同的AI处理器型号上，其支持的原型输入不同。 通过该接口，可针对不同的AI处理器型号注册差异化的算子原型。调用该接口后会返回一个OpParamDef结构，后续可通过该结构配置算子输入信息。”。《AutoContiguous》明确“配置该参数，当单算子API（aclnnxxx）接口中的输入（aclTensor类型）是非连续tensor时，框架会自动将其转换为连续tensor。 该接口仅在如下场景支持： - 通过单算子API执行的方式开发单算子调用应用。 - 间接调用单算子API\(aclnnxxx\)接口：Pytorch框架单算子直调的场景。”，可直接用于核对算子 Input/Output 原型、OpParamDef dtype/format/optional/value-depend 参数及已证注册故障。
- [OpParamDef](op_param_def.md)（`same_topic`）：AutoContiguous 是 OpParamDef 上的输入契约配置，需结合参数定义使用。
<!-- cannbot:related:end -->
