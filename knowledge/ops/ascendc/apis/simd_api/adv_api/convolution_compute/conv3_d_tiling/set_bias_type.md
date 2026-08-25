---
type: API
title: SetBiasType
description: 设置Bias在内存上的位置、数据格式和数据类型。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.neighborhood.convolution]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/convolution_compute/Conv3D_Tiling/SetBiasType.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# SetBiasType

设置Bias在内存上的位置、数据格式和数据类型。

函数原型：void SetBiasType(const ConvCommonApi::TPosition pos, const ConvCommonApi::ConvFormat format, const ConvCommonApi::ConvDtype dtype)

参数：
- pos（输入）：Bias在内存上的位置。当前仅支持TPosition::GM。
- format（输入）：Bias的数据格式。当前仅支持ConvFormat::ND。
- dtype（输入）：Bias的数据类型。当前仅支持ConvDtype::FLOAT16、ConvDtype::FLOAT。

<!-- cannbot:related:start -->
## 相关

- [L1与BiasTable Buffer数据搬运](../../../basic_api/data_move_guide/l1_bias_table_data_move.md)（`related`）：《L1与BiasTable Buffer数据搬运》说明DataCopy能够实现L1 Buffer至BiasTable Buffer的连续数据搬运，数据搬运时格式和内容保持不变。；《SetBiasType》说明设置Bias在内存上的位置、数据格式和数据类型。。二者在L1到BiasTable的连续搬运由C++/Tensor/C三层等价接口实现，并受Bias类型和数据通路约束上存在可执行的直接衔接。
- [SetBias](../conv3_d_kernel/set_bias.md)（`related`）：Conv3D kernel 的 SetBias 绑定 bias 张量，而 tiling 侧 SetBiasType 声明同一 bias 的 GM 位置、ND 格式和 dtype；两侧配置必须一致。
- [SetOutputType](set_output_type.md)（`related`）：《SetOutputType》的任务是“设置结果矩阵Output在内存上的位置、数据格式和数据类型。”。《SetBiasType》具体提供“设置Bias在内存上的位置、数据格式和数据类型。”，它直接用于Conv3D 输出位置/格式/dtype 在 Tiling 与 Kernel 间的一致性。
- [Conv3D模板参数](../conv3_d_kernel/conv3_d_template_params.md)（`same_topic`）：Conv3D模板参数 与《SetBiasType》的实质衔接是：Conv3D 模板参数决定 Input/Weight/Output/Bias 的位置、格式与类型，必须和 Kernel 构造、Init、Tiling 结构及 Set*Type/SetGroups 配置保持一致。
<!-- cannbot:related:end -->
