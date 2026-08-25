---
type: API
title: TensorDataType
description: AscendC::TensorDataType是ge::DataType的类型别名，用于描述高阶API的Host侧Tiling接口使用的Tensor数据类型。
  具体使用请参考ge::DataType。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/data_structures/TensorDataType.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# TensorDataType

## 功能说明

`AscendC::TensorDataType`是`ge::DataType`的类型别名，用于描述高阶API的Host侧Tiling接口使用的Tensor数据类型。

具体使用请参考[ge::DataType](https://gitcode.com/cann/metadef/blob/master/docs/api/ge_namespace/DataType.md)。

<!-- cannbot:related:start -->
## 相关

- [SetAType](../cube_compute/matmul_tiling/set_a_type.md)（`related`）：TensorDataType 与《SetAType》的实质衔接是：TensorDataType 与 TensorShape 都是高阶 API Host Tiling 公共类型；SetAType 的 dataType 参数展示该 ge::DataType 别名如何进入矩阵类型配置。
- [TensorShape](tensor_shape.md)（`related`）：TensorShape 与 TensorDataType 共同组成高阶 API Host Tiling 对输入张量的形状和类型描述契约。
- [DataTypeForBinQuery](../../../utils_api/prototype_register_management/op_param_def/data_type_for_bin_query.md)（`same_topic`）：DataTypeForBinQuery 与《TensorDataType》的实质衔接是：DataTypeForBinQuery 与 FormatForBinQuery 共同决定运行时二进制键；OpParamDef 的类型/格式列表、Version、Input 及 InferDataType 必须保持注册与推导一致。
- [数据结构](data_structures.md)（`same_topic`）：TensorDataType 与《数据结构》的实质衔接是：TensorDataType 与 TensorShape 都是高阶 API Host Tiling 公共类型；SetAType 的 dataType 参数展示该 ge::DataType 别名如何进入矩阵类型配置。
<!-- cannbot:related:end -->
