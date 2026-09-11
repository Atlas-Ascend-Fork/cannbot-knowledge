---
type: API
title: 卷积计算End
description: 在Conv3D计算完成后，必须调用一次End函数，以清除EventID并释放内部申请的临时内存。
tags:
- task.lookup
- topic.implementation.api_layer.high_level_api
- topic.compute.neighborhood.convolution
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/convolution_compute/Conv3D_Kernel/End.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- a2
- a3
---

# End

## 功能说明

在Conv3D计算完成后，必须调用一次End函数，以清除EventID并释放内部申请的临时内存。

## 函数原型

```
void End()
```

## 参数说明

无

## 返回值说明

无

## 约束说明

End接口必须在IterateAll接口后调用。

## 调用示例

```
conv3dApi.End();
```



<!-- cannbot:related:start -->
## 相关

- [IterateAll](iterate_all.md)（`related`）：焦点卡规定多 batch 时“多 batch 场景需逐 batch 调用 SetInput、IterateAll 和 End”，候选卡说明“在Conv3D计算完成后，必须调用一次End函数，以清除EventID并释放内部申请的临时内存。”；这把逐 batch 计算与资源收尾组成完整生命周期。

<!-- cannbot:api-operator:start -->
### 源码中使用此 API 的算子

展示 1 / 1 个已匹配算子；每个 API 最多展示 10 个自动关联。
范围为算子卡声明的固定版本源码文件中的直接调用，不代表所有编译分支均执行，也不保证覆盖间接调用。

- [QuantConvolution A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/nn/conv/quant_convolution.md)（`related`）：算子声明的固定版本源码包含对 `End(...)` 的直接调用（第 248 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/conv/conv3d_v2/op_kernel/conv3dv2.h#L248)

<!-- cannbot:api-operator:end -->
<!-- cannbot:related:end -->
