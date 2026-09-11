---
type: API
title: SetHF32
description: 在纯Cube模式（只有矩阵计算）下，设置是否开启HF32（矩阵乘计算时可采用的数据类型）模式。开启后，在矩阵乘计算时，float32数据类型会转换为hf32数据类型，可提升计算性能，但同时也会带来精度损失。
tags:
- task.lookup
- topic.implementation.api_layer.high_level_api
- topic.programming_model.execution_unit.cube
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/cube_compute/Matmul_Kernel/SetHF32.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- '950'
- a2
- a3
---

# SetHF32

## 功能说明

在纯Cube模式（只有矩阵计算）下，设置是否开启HF32（矩阵乘计算时可采用的数据类型）模式。开启后，在矩阵乘计算时，float32数据类型会转换为hf32数据类型，可提升计算性能，但同时也会带来精度损失。

## 函数原型

```
__aicore__ inline void SetHF32(bool enableHF32 = false, int32_t transMode = 0)
```

## 参数说明

| 参数名 | 输入/输出 | 描述 |
| --- | --- | --- |
| enableHF32 | 输入 | 配置是否开启HF32模式，默认值false(不开启)。 |
| transMode | 输入 | 配置在开启HF32模式时，float转换为hf32时所采用的ROUND模式。默认值0。<br><br>0：就近舍入，距离相等时向偶数进位。<br><br>1：就近舍入，距离相等时向远离0方向进位。 |

## 返回值说明

无

## 约束说明

本接口仅支持在纯Cube模式下调用。

## 调用示例

```
//纯Cube模式
#define ASCENDC_CUBE_ONLY
REGIST_MATMUL_OBJ(&pipe, GetSysWorkSpacePtr(), mm, &tiling);    //  A/B/C/BIAS类型是float
mm.SetTensorA(gm_a);
mm.SetTensorB(gm_b);
if (tiling.isBias) {
    mm.SetBias(gmBias);
}
mm.SetHF32(true);
mm.IterateAll(gm_c);
mm.SetHF32(false);
mm.End();
```


<!-- cannbot:related:start -->
## 相关

- [WeightQuantBatchMatmul 950 Direct Invoke 算子知识](../../../../../operators/direct/nn/matmul/weight_quant_batch_matmul_950.md)（`related`）：开启后，在矩阵乘计算时，float32数据类型会转换为hf32数据类型，可提升计算性能，但同时也会带来精度损失。；R-002 严格保持 FP32 反量化顺序：先把 X 转 FP32，把 `(W+offset)*scale` 转为 FP32 并由 `［K,N］` 写成 `［N,K］`，关闭 HF32；每 16 个 K 产生一个 FP32 `M×N` partial，用 FP32 Kahan 累积，最后加 bias 并 cast 一次。API 卡给出开启 HF32 的精度代价，算子卡明确在补偿 FP32 route 关闭它。

<!-- cannbot:api-operator:start -->
### 知识正文中的调用示例

展示 3 / 3 个已匹配算子；每个 API 最多展示 10 个自动关联。
以下仅有知识正文中的调用证据，未作为源码调用结果。

- [LSTM 950 Direct Invoke 算子知识](../../../../../operators/direct/nn/rnn/lstm_950.md)（`related`）：算子正文包含对 `SetHF32(...)` 的直接调用；本卡提供该接口契约。
- [MatmulAlltoAll 950 ACLNN 算子知识](../../../../../operators/aclnn/transformer/mc2/matmul_allto_all_950.md)（`related`）：算子正文包含对 `SetHF32(...)` 的直接调用；本卡提供该接口契约。
- [MhcPreSinkhorn A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/transformer/mhc/mhc_pre_sinkhorn.md)（`related`）：算子正文包含对 `SetHF32(...)` 的直接调用；本卡提供该接口契约。

<!-- cannbot:api-operator:end -->
<!-- cannbot:related:end -->
