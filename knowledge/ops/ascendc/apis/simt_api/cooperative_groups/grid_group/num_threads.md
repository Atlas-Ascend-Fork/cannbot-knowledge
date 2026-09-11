---
type: API
title: NumThreads
description: 获取当前Grid内的SIMT线程总数。
tags:
- task.lookup
- topic.implementation.api_layer.simt_api
- topic.programming_model.cooperative_groups
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/cooperative_groups/grid_group/num_threads.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- '950'
---

# num_threads

## 功能说明

获取当前Grid内的SIMT线程总数。

## 函数原型

```cpp
static unsigned long long num_threads()
```

## 参数说明

无

## 返回值说明

当前Grid内的SIMT线程总数。

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
        unsigned long long thread_num = g.num_threads();
        ...
    }
    ```


<!-- cannbot:related:start -->
## 相关

- [Grid协作组size](size.md)（`same_topic`）：获取当前Grid内的SIMT线程总数，与接口num_threads功能相同。；获取当前Grid内的SIMT线程总数。。Size 正文直接声明与 NumThreads 功能相同，两者都返回当前 Grid 的 SIMT 线程总数，是同一查询契约的两个接口名称。
<!-- cannbot:related:end -->
