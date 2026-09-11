---
type: API
title: ThreadRank
description: 获取当前线程在Grid内所有线程中的排名，排名从0开始计数。
tags:
- task.lookup
- topic.implementation.api_layer.simt_api
- topic.programming_model.cooperative_groups
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/cooperative_groups/grid_group/thread_rank.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- '950'
---

# thread_rank

## 功能说明

获取当前线程在Grid内所有线程中的排名，排名从0开始计数。

## 函数原型

```cpp
static unsigned long long thread_rank()
```

## 参数说明

无

## 返回值说明

当前线程在Grid内所有SIMT线程中的排名。

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
        unsigned long long rank = g.thread_rank();
        ...
    }
    ```
