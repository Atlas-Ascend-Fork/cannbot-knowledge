---
type: API
title: BlockIndex
description: 获取当前线程所属线程块在Grid中的三维索引。
tags:
- task.lookup
- topic.implementation.api_layer.simt_api
- topic.programming_model.cooperative_groups
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/cooperative_groups/grid_group/block_index.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- '950'
---

# block_index

## 功能说明

获取当前线程所属线程块在Grid中的三维索引。

## 函数原型

```cpp
static dim3 block_index()
```

## 参数说明

无

## 返回值说明

当前线程所属线程块在Grid中的三维索引。

## 约束说明

仅支持SIMT编程场景，不支持SIMD与SIMT混合编程场景。

## 调用示例

- SIMT编程场景：

    ```cpp
    using namespace cooperative_groups;
    __global__ void simt_kernel(...)
    {
        ...
        grid_group g = this_grid();
        dim3 block = g.block_index();
        ...
    }
    ```


<!-- cannbot:related:start -->
## 相关

- [多核共享首段行区间导致部分输出未写](../../../../runbooks/precision/multiblock_launch_must_derive_row_range_from_block_index.md)（`exemplifies`）：正确映射是 `mStart = blockIdx * rowsPerCore`，`mEnd = min(mStart + rowsPerCore, M)`；这里 `rowsPerCore = ceil(M / numBlocks)`。；获取当前线程所属线程块在Grid中的三维索引。。运行手册用 blockIdx 推导每个线程块负责的行区间并修复多块重复计算，BlockIndex 卡给出该索引在 Grid 中的语义，是索引 API 驱动任务划分的具体实例。
<!-- cannbot:related:end -->
