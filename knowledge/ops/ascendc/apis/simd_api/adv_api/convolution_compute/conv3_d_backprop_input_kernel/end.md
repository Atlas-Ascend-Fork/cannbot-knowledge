---
type: API
title: 卷积计算End
description: 在Conv3DBackpropInput卷积反向计算完成后，必须调用一次End，以清除EventID并释放内部申请的临时内存。
tags:
- task.lookup
- topic.implementation.api_layer.high_level_api
- topic.compute.neighborhood.convolution
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/convolution_compute/Conv3DBackpropInput_Kernel/End.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- a2
- a3
---

# End

## 功能说明

在Conv3DBackpropInput卷积反向计算完成后，必须调用一次End，以清除EventID并释放内部申请的临时内存。

## 函数原型

```
__aicore__ inline void End()
```

## 参数说明

无

## 返回值说明

无

## 约束说明

End接口必须在Iterate和GetTensorC接口后调用。

## 调用示例

```
const Conv3DBackpropInputTilingData* tilingData;
// ...初始化tilingData
ConvBackpropApi::Conv3DBackpropInput<weightDxType, inputSizeDxType, gradOutputDxType, gradInputDxType> gradInput_;
// ...其它调用
gradInput_.End();
```



<!-- cannbot:related:start -->
## 相关

- [Conv3DBackpropInput](conv3_d_backprop_input_usage.md)（`related`）：Ascend C提供一组Conv3DBackpropInput高阶API，便于用户快速实现卷积的反向运算，求解反向传播的误差。；在Conv3DBackpropInput卷积反向计算完成后，必须调用一次End，以清除EventID并释放内部申请的临时内存。。用法卡覆盖 Conv3DBackpropInput 任务，End 卡规定该任务完成后的必需清理步骤。
<!-- cannbot:related:end -->
