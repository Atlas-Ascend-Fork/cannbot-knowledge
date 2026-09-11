---
type: API
title: SetGradOutput
description: 设置卷积反向计算的输入矩阵GradOutput。
tags:
- task.lookup
- topic.implementation.api_layer.high_level_api
- topic.compute.neighborhood.convolution
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/convolution_compute/Conv3DBackpropInput_Kernel/SetGradOutput.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- a2
- a3
---

# SetGradOutput

## 功能说明

设置卷积反向计算的输入矩阵GradOutput。

## 函数原型

```
__aicore__ inline void SetGradOutput(const AscendC::GlobalTensor<SrcT>& gradOutput)
```

## 参数说明

**表1**  接口参数说明

| 参数名 | 输入/输出 | 描述 |
| --- | --- | --- |
| gradOutput | 输入 | GradOutput矩阵在Global Memory上的首地址。类型为[GlobalTensor](../../../basic_api/data_structures/global_tensor/index.md)。SrcT表示GradOutput矩阵的数据类型，当前支持的数据类型为：half、bfloat16_t。 |

## 返回值说明

无

## 约束说明

无

## 调用示例

```
ConvBackpropApi::Conv3DBackpropInput<weightDxType, inputSizeDxType, gradOutputDxType, gradInputDxType> gradInput_;
// 设置GradOutput中GlobalTensor的地址
GlobalTensor<gradOutputType> gradOutputGm_;
gradOutputGm_.SetGlobalBuffer((__gm__ gradOutputType*)gradOutput);
gradInput_.SetGradOutput(gradOutputGm_);
```


<!-- cannbot:related:start -->
## 相关

- [Conv3DBackpropInput](conv3_d_backprop_input_usage.md)（`related`）：设置卷积反向计算的输入矩阵GradOutput。；Conv3DBackpropInput 以 GradOutput 和转置后的 Weight 为输入，计算特征矩阵的反向传播误差 GradInput。。SetGradOutput 卡指定写入卷积反向计算的 GradOutput 输入，使用说明卡给出该输入与转置 Weight 共同计算 GradInput 的数学角色，因此参数设置可直接落到完整反向运算链。
<!-- cannbot:related:end -->
