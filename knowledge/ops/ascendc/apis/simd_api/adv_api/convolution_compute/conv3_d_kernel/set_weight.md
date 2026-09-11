---
type: API
title: SetWeight
description: 设置权重矩阵Weight。
tags:
- task.lookup
- topic.implementation.api_layer.high_level_api
- topic.compute.neighborhood.convolution
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/convolution_compute/Conv3D_Kernel/SetWeight.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- a2
- a3
---

# SetWeight

## 功能说明

设置权重矩阵Weight。

## 函数原型

```
__aicore__ inline void SetWeight(const AscendC::GlobalTensor<WeightT>& weight)
```

## 参数说明

| 参数名 | 输入/输出 | 描述 |
| --- | --- | --- |
| weight | 输入 | Weight在Global Memory上的地址。类型为[GlobalTensor](../../../basic_api/data_structures/global_tensor/index.md)。权重矩阵Weight支持的数据类型为：half、bfloat16_t。 |

## 返回值说明

无

## 约束说明

无

## 调用示例

```
GlobalTensor<half> weightGm;
weightGm.SetGlobalBuffer(reinterpret_cast<__gm__ half*>(weight));
conv3dApi.SetWeight(weightGm);
```


<!-- cannbot:related:start -->
## 相关

- [IterateAll](iterate_all.md)（`related`）：SetWeight 的动作是“设置权重矩阵Weight。”；IterateAll 规定“IterateAll接口必须在初始化接口及输入输出配置接口之后进行调用”。权重配置属于启动单核 Conv3D 计算前必须完成的输入配置。

<!-- cannbot:api-operator:start -->
### 源码中使用此 API 的算子

展示 1 / 1 个已匹配算子；每个 API 最多展示 10 个自动关联。
范围为算子卡声明的固定版本源码文件中的直接调用，不代表所有编译分支均执行，也不保证覆盖间接调用。

- [QuantConvolution A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/nn/conv/quant_convolution.md)（`related`）：算子声明的固定版本源码包含对 `SetWeight(...)` 的直接调用（第 230 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/conv/conv3d_v2/op_kernel/conv3dv2.h#L230)

<!-- cannbot:api-operator:end -->
<!-- cannbot:related:end -->
