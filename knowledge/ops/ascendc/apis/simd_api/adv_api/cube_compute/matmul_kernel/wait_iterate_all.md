---
type: API
title: WaitIterateAll
description: 等待IterateAll异步接口返回，支持连续输出到Global Memory。
tags:
- task.lookup
- topic.implementation.api_layer.high_level_api
- topic.programming_model.execution_unit.cube
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/cube_compute/Matmul_Kernel/WaitIterateAll.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- '950'
- a2
- a3
- kirin_x90
source_headers:
- include/adv_api/matmul/matmul_client.h
---

# WaitIterateAll

## 功能说明

等待IterateAll异步接口返回，支持连续输出到Global Memory。

## 函数原型

```
__aicore__ inline void WaitIterateAll()
```

## 参数说明

无

## 返回值说明

无

## 约束说明

-   配套[IterateAll](iterate_all.md)异步接口使用。
-   仅支持连续输出至Global Memory。

## 调用示例

```
AscendC::Matmul<aType, bType, cType, biasType> mm;
mm.SetTensorA(gm_a[offsetA]);
mm.SetTensorB(gm_b[offsetB]);
if (tiling.isBias) {
    mm.SetBias(gm_bias[offsetBias]);
}
mm.template IterateAll<false>(gm_c[offsetC], 0, false, true);
// do some others compute
mm.WaitIterateAll(); // 等待IterateAll完成
```


<!-- cannbot:related:start -->
## 相关

- [IterateAll](iterate_all.md)（`related`）：异步：不需要同步等待IterateAll执行结束。；等待IterateAll异步接口返回，支持连续输出到Global Memory。。左卡允许 IterateAll 以 sync=false 发起异步矩阵计算，右卡负责等待该异步调用完成；两端给出发起与完成等待的直接生命周期顺序。

<!-- cannbot:api-operator:start -->
### 知识正文中的调用示例

展示 1 / 1 个已匹配算子；每个 API 最多展示 10 个自动关联。
以下仅有知识正文中的调用证据，未作为源码调用结果。

- [grouped_matmul_add A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/transformer/gmm/grouped_matmul_add.md)（`related`）：算子正文包含对 `WaitIterateAll(...)` 的直接调用；本卡提供该接口契约。

<!-- cannbot:api-operator:end -->
<!-- cannbot:related:end -->
