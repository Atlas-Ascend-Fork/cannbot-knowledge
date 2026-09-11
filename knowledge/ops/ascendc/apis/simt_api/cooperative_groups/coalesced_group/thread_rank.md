---
type: API
title: ThreadRank
description: 获取当前线程在coalesced_group组内的排名，排名从0开始。
tags:
- task.lookup
- topic.implementation.api_layer.simt_api
- topic.programming_model.cooperative_groups
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/cooperative_groups/coalesced_group/thread_rank.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- '950'
---

# thread_rank

## 功能说明

获取当前线程在`coalesced_group`组内的排名，排名从0开始。

## 函数原型

```cpp
unsigned int thread_rank() const
```

## 参数说明

无

## 返回值说明

当前线程在`coalesced_group`组内的排名。

## 约束说明

无

## 调用示例

示例代码中的条件分支将一个warp中所有线程id是偶数的线程组成`coalesced_group`协作组，组内各线程`thread_rank`接口返回结果如下图所示。

**图1**  coalesced_group组内各线程rank  
![](https://raw.gitcode.com/cann/asc-devkit/raw/885973fe9fd42a600e3551af9bc11a279e6f183b/docs/zh/api/figures/coalesced_group_rank.png "coalesced_group_rank")

- SIMT编程场景：

    ```cpp
    using namespace cooperative_groups;
    __global__ void simt_kernel(...)
    {
        ...
        if (threadIdx.x % 2 == 0) {
            coalesced_group active = coalesced_threads();
            unsigned int rank = active.thread_rank();
        }
        ...
    }
    ```

- SIMD与SIMT混合编程场景：

    ```cpp
    using namespace cooperative_groups;
    __simt_vf__ inline void simt_kernel(...)
    {
        ...
        if (threadIdx.x % 2 == 0) {
            coalesced_group active = coalesced_threads();
            unsigned int rank = active.thread_rank();
        }
        ...
    }
    ```
