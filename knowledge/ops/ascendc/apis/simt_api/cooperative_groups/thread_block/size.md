---
type: API
title: ThreadBlock协作组size
description: 获取当前线程所属线程块内的线程总数，与接口num_threads功能相同。
tags:
- task.lookup
- topic.implementation.api_layer.simt_api
- topic.programming_model.cooperative_groups
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/cooperative_groups/thread_block/size.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- '950'
---

# size

## 功能说明

获取当前线程所属线程块内的线程总数，与接口[num_threads](num_threads.md)功能相同。

## 函数原型

```cpp
static unsigned int size()
```

## 参数说明

无

## 返回值说明

当前线程所属线程块内的线程总数。

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
        unsigned int thread_num = g.size();
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
        unsigned int thread_num = g.size();
        ...
    }
    ```

<!-- cannbot:related:start -->
## 相关

- [NumThreads](num_threads.md)（`same_topic`）：获取当前线程所属线程块内的线程总数。；获取当前线程所属线程块内的线程总数，与接口num_threads功能相同。。size 正文明确声明与 num_threads 功能相同，两卡是同一 thread_block 线程数查询的两个接口名。
<!-- cannbot:related:end -->
