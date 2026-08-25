---
type: API
title: SetBiasType
description: 设置Bias的位置，数据格式，数据类型等信息，这些信息需要和kernel侧的设置保持一致。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/cube_compute/Matmul_Tiling/SetBiasType.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---


# SetBiasType

设置Bias的位置，数据格式，数据类型等信息，这些信息需要和kernel侧的设置保持一致。

参数：
- pos（输入）：Bias矩阵所在的buffer位置，可设置为：TPosition::GM, TPosition::VECOUT, TPosition::TSCM。
- type（输入）：Bias矩阵的数据格式，可设置为：CubeFormat::ND。
- dataType（输入）：Bias矩阵的数据类型，可设置为：DataType::DT_FLOAT、DataType::DT_FLOAT16、DataType::DT_INT32、DataType::DT_BFLOAT16。

返回值：-1表示设置失败； 0表示设置成功。

<!-- cannbot:related:start -->
## 相关

- [EnableBias](enable_bias.md)（`same_topic`）：SetBiasType 声明 bias 的位置、格式和 dtype，必须与 EnableBias 和 Kernel 实际输入一致。
- [SetBias](../matmul_kernel/set_bias.md)（`same_topic`）：焦点处理Matmul SetBias 的启用/禁用状态、Tiling 类型一致性与调用时机；SetBiasType正文说明“设置Bias的位置，数据格式，数据类型等信息，这些信息需要和kernel侧的设置保持一致”。候选决定 Bias 是否参与、Host/Kernel 类型是否一致，或界定 SetBias 必须发生在迭代前。
<!-- cannbot:related:end -->
