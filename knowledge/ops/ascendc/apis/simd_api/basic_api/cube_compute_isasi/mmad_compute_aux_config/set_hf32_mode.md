---
type: API
title: SetHF32Mode
description: 用于设置Mmad计算是否开启HF32模式，开启该模式后L0A Buffer/L0B Buffer中的FP32数据将在参与Mmad计算之前被舍入为HF32。
tags:
- task.lookup
- topic.implementation.api_layer.basic_api
- topic.programming_model.execution_unit.cube
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/mmad_compute_aux_config/SetHF32Mode.md
  role: primary
created_at: '2026-09-03T08:52:46Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- '950'
- a2
- a3
source_headers:
- include/basic_api/kernel_operator_mm_intf.h
---

# SetHF32Mode

## 功能说明

用于设置Mmad计算是否开启HF32模式，开启该模式后L0A Buffer/L0B Buffer中的FP32数据将在参与Mmad计算之前被舍入为HF32。

## 函数原型

```cpp
__aicore__ inline void SetHF32Mode(HF32Mode mode)
```

## 参数说明

**表1** 参数说明

| 参数名 | 输入/输出 | 描述 |
| --- | --- | --- |
| mode | 输入 | Mmad HF32模式控制入参，HF32Mode枚举类型。支持如下两种取值：<br>&nbsp;&nbsp;&bull; ENABLE：L0A Buffer/L0B Buffer中的FP32数据将在矩阵乘法之前被舍入为HF32。<br>&nbsp;&nbsp;&bull; DISABLE：将执行常规的FP32矩阵乘法。 |

## 返回值说明

无

## 约束说明

无

## 调用示例

```cpp
AscendC::SetHF32Mode(HF32Mode::ENABLE); // 控制mmad计算时是否使用HF32精度进行计算。
```


<!-- cannbot:related:start -->
## 相关

- [Cube计算(ISASI)HF32](../mmad_compute_key_features/hf32.md)（`related`）：HF32 特性卡说明“通过 SetHF32Mode 开启，舍入模式通过 SetHF32TransMode 配置（NEAREST_ZERO 或 NEAREST_EVEN）。”；SetHF32Mode 卡规定“设置 Mmad 计算是否开启 HF32 模式。开启后 L0A Buffer/L0B Buffer 中的 FP32 数据将在参与 Mmad 计算前被舍入为 HF32（half-fp32），可使 f322f32 计算性能提升 2 倍，但有精度损失。”，形成使能开关及其性能/精度后果的直接调用链。
- [SetHF32TransMode](set_hf32_trans_mode.md)（`related`）：设置 Mmad 计算是否开启 HF32 模式。开启后 L0A Buffer/L0B Buffer 中的 FP32 数据将在参与 Mmad 计算前被舍入为 HF32（half-fp32），可使 f322f32 计算性能提升 2 倍，但有精度损失。；设置 HF32 模式下 FP32 到 HF32 的取整方式。须先调用 SetHF32Mode 开启 HF32 模式。。SetHF32Mode 负责启用 Mmad 的 HF32 舍入路径，SetHF32TransMode 依赖前者并配置该路径采用的具体取整规则。

<!-- cannbot:api-operator:start -->
### 源码中使用此 API 的算子

展示 1 / 1 个已匹配算子；每个 API 最多展示 10 个自动关联。
范围为算子卡声明的固定版本源码文件中的直接调用，不代表所有编译分支均执行，也不保证覆盖间接调用。

- [MhcPreSinkhorn A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/transformer/mhc/mhc_pre_sinkhorn.md)（`related`）：算子声明的固定版本源码包含对 `SetHF32Mode(...)` 的直接调用（第 468 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/mhc/mhc_pre_sinkhorn/op_kernel/mhc_pre_sinkhorn_cube_compute.h#L468)

### 知识正文中的调用示例

展示 1 / 1 个已匹配算子；每个 API 最多展示 10 个自动关联。
以下仅有知识正文中的调用证据，未作为源码调用结果。

- [Conv2D 950 Direct Invoke 算子知识](../../../../../operators/direct/nn/conv/conv_2d_950.md)（`related`）：算子正文包含对 `SetHF32Mode(...)` 的直接调用；本卡提供该接口契约。

<!-- cannbot:api-operator:end -->
<!-- cannbot:related:end -->
