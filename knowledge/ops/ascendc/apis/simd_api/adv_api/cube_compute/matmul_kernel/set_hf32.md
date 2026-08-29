---
type: API
title: SetHF32
description: 在纯Cube模式（只有矩阵计算）下，设置是否开启HF32（矩阵乘计算时可采用的数据类型）模式。开启后，在矩阵乘计算时，float32数据类型会转换为hf32数据类型，可提升计算性能，但同时也会带来精度损失。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/cube_compute/Matmul_Kernel/SetHF32.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# SetHF32

在纯Cube模式（只有矩阵计算）下，设置是否开启HF32（矩阵乘计算时可采用的数据类型）模式。开启后，在矩阵乘计算时，float32数据类型会转换为hf32数据类型，可提升计算性能，但同时也会带来精度损失。

函数原型：__aicore__ inline void SetHF32(bool enableHF32 = false, int32_t transMode = 0)

参数：
- enableHF32（输入）：配置是否开启HF32模式，默认值false(不开启)。
- transMode（输入）：配置在开启HF32模式时，float转换为hf32时所采用的ROUND模式。默认值0。 0：就近舍入，距离相等时向偶数进位。 1：就近舍入，距离相等时向远离0方向进位。

支持：Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品。不支持：Atlas 200I/500 A2 推理产品、Atlas 推理系列产品AI Core、Atlas 推理系列产品Vector Core、Atlas 训练系列产品、Kirin X90、Kirin 9030。

<!-- cannbot:related:start -->
## 相关

- [WeightQuantBatchMatmul 950 Direct Invoke 算子知识](../../../../../operators/direct/nn/matmul/weight_quant_batch_matmul_950.md)（`related`）：开启后，在矩阵乘计算时，float32数据类型会转换为hf32数据类型，可提升计算性能，但同时也会带来精度损失。；R-002 严格保持 FP32 反量化顺序：先把 X 转 FP32，把 `(W+offset)*scale` 转为 FP32 并由 `［K,N］` 写成 `［N,K］`，关闭 HF32；每 16 个 K 产生一个 FP32 `M×N` partial，用 FP32 Kahan 累积，最后加 bias 并 cast 一次。API 卡给出开启 HF32 的精度代价，算子卡明确在补偿 FP32 route 关闭它。
<!-- cannbot:related:end -->
