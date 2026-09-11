---
type: API
title: SetBias
description: 设置偏置矩阵Bias。
tags:
- task.lookup
- topic.implementation.api_layer.high_level_api
- topic.compute.neighborhood.convolution
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/convolution_compute/Conv3D_Kernel/SetBias.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- a2
- a3
---

# SetBias

## 功能说明

设置偏置矩阵Bias。

## 函数原型

```
__aicore__ inline void SetBias(const AscendC::GlobalTensor<BiasT>& bias)
```

## 参数说明

| 参数名 | 输入/输出 | 描述 |
| --- | --- | --- |
| bias | 输入 | Bias在Global Memory上的地址。类型为[GlobalTensor](../../../basic_api/data_structures/global_tensor/index.md)。偏置矩阵Bias支持的数据类型为：half、bfloat16_t。 |

## 返回值说明

无

## 约束说明

在卷积计算中，如果涉及偏置矩阵Bias，必须调用此接口；若卷积计算不涉及Bias，则不应调用此接口。

## 调用示例

```
GlobalTensor<float> biasGm;
biasGm.SetGlobalBuffer(reinterpret_cast<__gm__ half*>(bias));
if (biasFlag) {
    conv3dApi.SetBias(biasGm);
}
```


<!-- cannbot:related:start -->
## 相关

- [Conv3DUsage](conv3_d_usage.md)（`related`）：bias（输入）：Bias在Global Memory上的地址。类型为GlobalTensor。偏置矩阵Bias支持的数据类型为：half、bfloat16_t。；B为Conv3D卷积的偏置矩阵Bias。 - Y为完成卷积及偏置操作之后的结果矩阵Output。。SetBias 的输入合同把 usage 中卷积偏置 B 的 GM 地址和支持 dtype 落到具体配置接口。
- [SetBiasType](../conv3_d_tiling/set_bias_type.md)（`related`）：bias（输入）：Bias在Global Memory上的地址。类型为GlobalTensor。偏置矩阵Bias支持的数据类型为：half、bfloat16_t。；设置Bias在内存上的位置、数据格式和数据类型。。tiling 侧先声明 Bias 的位置、格式和类型，kernel 侧 SetBias 再接收相应 GM tensor，形成 Host 配置到 Device 入参的合同。

<!-- cannbot:api-operator:start -->
### 源码中使用此 API 的算子

展示 1 / 1 个已匹配算子；每个 API 最多展示 10 个自动关联。
范围为算子卡声明的固定版本源码文件中的直接调用，不代表所有编译分支均执行，也不保证覆盖间接调用。

- [QuantConvolution A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/nn/conv/quant_convolution.md)（`related`）：算子声明的固定版本源码包含对 `SetBias(...)` 的直接调用（第 232 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/conv/conv3d_v2/op_kernel/conv3dv2.h#L232)

<!-- cannbot:api-operator:end -->
<!-- cannbot:related:end -->
