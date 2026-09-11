---
type: API
title: GroupDim
description: 获取当前线程所属线程块的线程配置，与接口dim_threads功能相同。
tags:
- task.lookup
- topic.implementation.api_layer.simt_api
- topic.programming_model.cooperative_groups
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/cooperative_groups/thread_block/group_dim.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- '950'
---

# group_dim

## 功能说明

获取当前线程所属线程块的线程配置，与接口[dim_threads](dim_threads.md)功能相同。

## 函数原型

```cpp
static dim3 group_dim()
```

## 参数说明

无

## 返回值说明

当前线程所属线程块的线程配置。

## 约束说明

无

## 调用示例

- SIMT编程场景：

    ```cpp
    using namespace cooperative_groups;
    __global__ void simt_kernel(...)
    {
        ...
        thread_block g = this_thread_block();
        dim3 block_dim = g.group_dim();
        ...
    }
    ```

- SIMD与SIMT混合编程场景：

    ```cpp
    using namespace cooperative_groups;
    __simt_vf__ inline void simt_kernel(...)
    {
        ...
        thread_block g = this_thread_block();
        dim3 block_dim = g.group_dim();
        ...
    }
    ```

<!-- cannbot:related:start -->
## 相关

- [DimThreads](dim_threads.md)（`same_topic`）：“获取当前线程所属线程块的线程配置，返回值与内置变量blockDim相同。”给出焦点端事实；“获取当前线程所属线程块的线程配置，与接口dim_threads功能相同。”给出候选端事实。候选卡明确声明 group_dim 与 dim_threads 功能相同，两端是同一线程块维度查询合同的两个接口名。
<!-- cannbot:related:end -->
