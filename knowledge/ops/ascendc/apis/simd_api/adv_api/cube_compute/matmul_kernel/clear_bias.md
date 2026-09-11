---
type: API
title: ClearBias
description: DisableBias接口与该接口的功能相同，建议使用DisableBias。 清除Bias标志位，表示Matmul计算时没有Bias参与。如果在调用Init时配置了TCubeTiling结构中的isBias参数来启用Bias，调用该接口后，会清除Bias标志位，不再启用Bias。
tags:
- task.lookup
- topic.implementation.api_layer.high_level_api
- topic.programming_model.execution_unit.cube
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/cube_compute/Matmul_Kernel/ClearBias.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- '950'
- a2
- a3
- 310p
- kirin_x90
---

# ClearBias

## 功能说明

[DisableBias](disable_bias.md)接口与该接口的功能相同，建议使用[DisableBias](disable_bias.md)。

清除Bias标志位，表示Matmul计算时没有Bias参与。如果在调用[Init](init.md)时配置了TCubeTiling结构中的isBias参数来启用Bias，调用该接口后，会清除Bias标志位，不再启用Bias。

## 函数原型

```
__aicore__ inline void ClearBias()
```

## 参数说明

无

## 返回值说明

无

## 约束说明

无

## 调用示例

```
REGIST_MATMUL_OBJ(&pipe, GetSysWorkSpacePtr(), mm, &tiling);
mm.SetTensorA(gm_a);
mm.SetTensorB(gm_b);
mm.ClearBias();    // 清除tiling中的Bias标志位
mm.IterateAll(gm_c);
```


<!-- cannbot:related:start -->
## 相关

- [Init](init.md)（`related`）：Init 页说明“Init主要用于对Matmul对象中的Tiling数据进行初始化，根据Tiling参数进行资源划分”；ClearBias 页明确“如果在调用［Init］(init.md)时配置了TCubeTiling结构中的isBias参数来启用Bias，调用该接口后，会清除Bias标志位，不再启用Bias。”，后者直接修改前者初始化出的 bias 状态。
- [DisableBias](disable_bias.md)（`same_topic`）：DisableBias接口与该接口的功能相同，建议使用DisableBias。 清除Bias标志位，表示Matmul计算时没有Bias参与。；清除Bias标志位，表示Matmul计算时没有Bias参与。。焦点卡明确将同功能旧入口迁移为候选 DisableBias。
<!-- cannbot:related:end -->
