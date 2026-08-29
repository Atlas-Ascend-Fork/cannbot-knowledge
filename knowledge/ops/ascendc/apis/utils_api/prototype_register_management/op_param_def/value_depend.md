---
type: API
title: ValueDepend
description: 标识该输入是否为“数据依赖输入”，数据依赖输入是指在Tiling/InferShape等函数实现时依赖该输入的具体数据。该输入数据为host侧数据，开发者在Tiling函数/InferShape函数中可以通过TilingContext类的GetInputTensor/InferShapeContext类的GetInputTensor获取这个输入数据。
tags: [task.lookup, topic.implementation.api_layer.utils_api, topic.implementation.operator_registration]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/prototype_register_management/OpParamDef/ValueDepend.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---
# ValueDepend

## 功能说明
标识该输入是否为“数据依赖输入”，数据依赖输入是指在Tiling/InferShape等函数实现时依赖该输入的具体数据。该输入数据为host侧数据，开发者在Tiling函数/InferShape函数中可以通过TilingContext类的GetInputTensor/InferShapeContext类的GetInputTensor获取这个输入数据。
## 函数原型
## 参数说明
value_depend：输入：REQUIRED：表示算子的输入必须是Const类型。在调用算子的SetCheckSupport时，会校验算子的输入是否是Const类型。若校验通过，则将此输入的值下发到算子；否则报错。OPTIONAL：表示算子的输入可以是Const类型，也可以不是Const类型。如果输入是Const类型，则将输入的值下发到算子，否则不下发。
scope：输入：ALL：指在Tiling/InferShape等函数实现时都依赖该输入的具体数据，行为与调用单参数ValueDepend重载接口一致。TILING：指仅在Tiling时依赖Tensor的值，可以支持Tiling下沉。
## 返回值说明
OpParamDef算子定义，OpParamDef请参考OpParamDef。
## 约束说明
仅支持对算子输入配置，输入的参数数据类型可以配置为DT_FLOAT/DT_BOOL/DT_INT64/DT_UINT64/DT_INT32/DT_UINT32/DT_INT16/DT_UINT16/DT_INT8/DT_UINT8，且必须满足以下三种情况之一：
1. 输入的参数数据类型配置全为DT_FLOAT，对应生成的输出类型aclFloatArray（aclnn数据类型）。
2. 输入的参数数据类型配置全为DT_BOOL，对应生成的输出类型aclBoolArray（aclnn数据类型）。
3. 输入的参数数据类型配置全为整数类型，即DT_INT64/DT_UINT64/DT_INT32/DT_UINT32/DT_INT16/DT_UINT16/DT_INT8/DT_UINT8，对应生成的输出类型aclIntArray（aclnn数据类型）。当数据类型配置含有DT_INT64以外的数据类型时，需要增加一组DT_INT64对应的输入/输出数据类型组合。

<!-- cannbot:related:start -->
## 相关

- [ValueDepend(REQUIRED) 让 axes 走 host 端](../../../../runbooks/compilation/opdef_value_depend_required_for_axes_host_read.md)（`exemplifies`）：“- reduce / split / topk 等带 Const 索引输入（axes/k/indices）的算子，若 TilingFunc 要读这些数值决定 tiling，必须在 OpDef 的 Input 上注 `.ValueDepend(REQUIRED)`，不能默认框架会拷数据。”；“REQUIRED：表示算子的输入必须是Const类型。在调用算子的SetCheckSupport时，会校验算子的输入是否是Const类型。若校验通过，则将此输入的值下发到算子；否则报错。”。API 合同解释运行手册修复为何能把 axes 值下发到 Host。
- [开启Tiling下沉](../../../../guides/programming_guide/advanced_programming/operator_graph_development/enable_tiling_sink.md)（`explains`）：本示例中的输入y通过ValueDepend配置了非Const类型的Tiling值依赖。；scope：输入：ALL：指在Tiling/InferShape等函数实现时都依赖该输入的具体数据，行为与调用单参数ValueDepend重载接口一致。TILING：指仅在Tiling时依赖Tensor的值，可以支持Tiling下沉。。指南以非 Const 输入 y 示范 ValueDepend 的 TILING 数据依赖，接口卡给出 ALL 与 TILING 的精确范围以及下沉能力。
- [StridedSliceAssignV2 A2/A3 ACLNN 算子知识](../../../../operators/aclnn/math/conversion/strided_slice_assign_v2.md)（`related`）：OpDef 对所有输入、输出标记 `AutoContiguous()`；`begin/end/strides/axes` 同时标记 `ValueDepend(REQUIRED)`，使 Tiling 在 Host 侧取得常量值。；标识该输入是否为“数据依赖输入”，数据依赖输入是指在Tiling/InferShape等函数实现时依赖该输入的具体数据。该输入数据为host侧数据，开发者在Tiling函数/InferShape函数中可以通过TilingContext类的GetInputTensor/InferShapeContext类的GetInputTensor获取这个输入数据。。算子卡实际把 begin/end/strides/axes 声明为 ValueDepend(REQUIRED)，API 卡解释该声明使 Host Tiling/InferShape 能读取输入具体值，形成注册到 Host 消费的合同。
<!-- cannbot:related:end -->
