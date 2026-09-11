---
type: API
title: DimBlocks
description: 获取当前Grid的线程块维度配置。
tags:
- task.lookup
- topic.implementation.api_layer.simt_api
- topic.programming_model.cooperative_groups
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/cooperative_groups/grid_group/dim_blocks.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- '950'
---

# dim_blocks

## 功能说明

获取当前Grid的线程块维度配置。

## 函数原型

```cpp
static dim3 dim_blocks()
```

## 参数说明

无

## 返回值说明

当前Grid的线程块维度配置。

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
        dim3 grid_dim = g.dim_blocks();
        ...
    }
    ```


<!-- cannbot:related:start -->
## 相关

- [GroupDim](group_dim.md)（`same_topic`）：获取当前Grid的线程块维度配置。；获取当前Grid的线程块维度配置，与接口dim_blocks功能相同。。两卡明确返回相同 Grid 线程块维度，group_dim 是 dim_blocks 的同功能接口。
<!-- cannbot:related:end -->
