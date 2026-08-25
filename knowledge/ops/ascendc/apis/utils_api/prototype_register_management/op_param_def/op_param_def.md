---
type: API
title: OpParamDef
description: OpParamDef算子参数定义接口索引。
tags: [task.lookup, topic.implementation.operator_registration]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/prototype_register_management/OpParamDef/OpParamDef.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# OpParamDef

OpParamDef 用于定义算子的输入输出张量参数，包括参数类型（ParamType）、数据类型（DataType、DataTypeList）、格式（Format、FormatList）、标量与标量列表（Scalar、ScalarList）等属性。还支持值依赖（ValueDepend）、连续性控制（IgnoreContiguous、AutoContiguous）、版本管理（Version）、初始值（InitValue）和参数跟随（Follow）等高级配置。

<!-- cannbot:related:start -->
## 相关

- [ACLNN 561000 非连续张量需 AutoContiguous](../../../../runbooks/compilation/aclnn_561000_autocontiguous.md)（`exemplifies`）：ACLNN 561000 非连续张量需 AutoContiguous 与《OpParamDef》的实质衔接是：561000 来自 OpParamDef 未声明连续性策略；AutoContiguous/IgnoreContiguous、Input/OpDef 和非连续 Load/Store/Slice/Transpose 卡共同决定转换还是保留 strides。
- [IgnoreContiguous](ignore_contiguous.md)（`related`）：IgnoreContiguous 与《OpParamDef》的实质衔接是：IgnoreContiguous 与 AutoContiguous 是非连续 aclTensor 的两种 OpParamDef 策略，561000 故障给出缺失配置时的可复现实例。
- [AutoContiguous](auto_contiguous.md)（`same_topic`）：AutoContiguous 是 OpParamDef 上的输入契约配置，需结合参数定义使用。
- [Comment](comment.md)（`same_topic`）：Comment 与《OpParamDef》的实质衔接是：Comment 写入 OpParamDef 的 input/output 注释并传播到自动生成原型和文档；构造、Input/Output、OpDef 与另一注册层 Comment 是同一元数据链。
- [DataTypeForBinQuery](data_type_for_bin_query.md)（`same_topic`）：DataTypeForBinQuery 与《OpParamDef》的实质衔接是：DataTypeForBinQuery 与 FormatForBinQuery 共同决定运行时二进制键；OpParamDef 的类型/格式列表、Version、Input 及 InferDataType 必须保持注册与推导一致。
- [DataType（OpParamDef）](data_type.md)（`same_topic`）：DataType 是 OpParamDef 的链式配置。
- [Follow（OpParamDef）](follow.md)（`same_topic`）：Follow 是 OpParamDef 的链式配置。
- [Input（原型注册管理）](../op_ai_core_config/input.md)（`same_topic`）：《Input（原型注册管理）》处理“某些场景下，同一个算子在不同的AI处理器型号上，其支持的原型输入不同。 通过该接口，可针对不同的AI处理器型号注册差异化的算子原型。调用该接口后会返回一个OpParamDef结构，后续可通过该结构配置算子输入信息。”。《OpParamDef》明确“OpParamDef算子参数定义接口索引。”，可直接用于核对算子 Input/Output 原型、OpParamDef dtype/format/optional/value-depend 参数及已证注册故障。
<!-- cannbot:related:end -->
