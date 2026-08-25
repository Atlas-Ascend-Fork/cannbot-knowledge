---
type: API
title: IgnoreContiguous
description: 某些算子支持非连续的tensor，在算子的实现中对非连续的tensor做了转换处理。配置该参数后，框架会忽略对非连续的校验。
tags: [task.lookup, topic.implementation.api_layer.utils_api, topic.implementation.operator_registration]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/prototype_register_management/OpParamDef/IgnoreContiguous.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# IgnoreContiguous

## 功能说明
某些算子支持非连续的tensor，在算子的实现中对非连续的tensor做了转换处理。配置该参数后，框架会忽略对非连续的校验。
## 函数原型
## 参数说明
无
## 返回值说明
OpParamDef算子定义，OpParamDef请参考OpParamDef。
## 约束说明
无

<!-- cannbot:related:start -->
## 相关

- [ACLNN 561000 非连续张量需 AutoContiguous](../../../../runbooks/compilation/aclnn_561000_autocontiguous.md)（`exemplifies`）：ACLNN 561000 非连续张量需 AutoContiguous 与《IgnoreContiguous》的实质衔接是：561000 来自 OpParamDef 未声明连续性策略；AutoContiguous/IgnoreContiguous、Input/OpDef 和非连续 Load/Store/Slice/Transpose 卡共同决定转换还是保留 strides。
- [MulPreferContiguous 稀疏广播拦截失败且慢于 304](../../../../runbooks/performance/mulprefercontiguous_304.md)（`exemplifies`）：《MulPreferContiguous 稀疏广播拦截失败且慢于 304》处理“B 类稀疏广播（首轴稀疏、stride 大）触发 MulPreferContiguous 拦截转连续，baseline GetWorkspaceSize 返回 -1.0（schMode 空）或性能慢于 fixed 直接走 304 nddma_transpose_noLoop。”。《IgnoreContiguous》提供“某些算子支持非连续的tensor，在算子的实现中对非连续的tensor做了转换处理。配置该参数后，框架会忽略对非连续的校验。”，其具体合同或探针直接接入稀疏广播输入的 contiguous 拦截、304 路由和非连续 shape/stride 合同。
- [AutoContiguous](auto_contiguous.md)（`related`）：IgnoreContiguous 与《AutoContiguous》的实质衔接是：IgnoreContiguous 与 AutoContiguous 是非连续 aclTensor 的两种 OpParamDef 策略，561000 故障给出缺失配置时的可复现实例。
- [OpParamDef](op_param_def.md)（`related`）：IgnoreContiguous 与《OpParamDef》的实质衔接是：IgnoreContiguous 与 AutoContiguous 是非连续 aclTensor 的两种 OpParamDef 策略，561000 故障给出缺失配置时的可复现实例。
<!-- cannbot:related:end -->
