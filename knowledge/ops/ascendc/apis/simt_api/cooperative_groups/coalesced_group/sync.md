---
type: API
title: CoalescedGroup协作组sync
description: 同步coalesced_group组内所有线程。
tags:
- task.lookup
- topic.implementation.api_layer.simt_api
- topic.programming_model.cooperative_groups
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/cooperative_groups/coalesced_group/sync.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- '950'
---

# sync

## 功能说明

同步`coalesced_group`组内所有线程。

## 函数原型

```cpp
void sync() const
```

## 参数说明

无

## 返回值说明

无

## 约束说明

必须保证`coalesced_group`组内所有线程都能执行到同一个`sync()`调用，否则是未定义行为。

## 调用示例

- SIMT编程场景：

    ```cpp
    using namespace cooperative_groups;
    __global__ void simt_kernel(...)
    {
        ...
        if (threadIdx.x % 2 == 0) {
            coalesced_group active = coalesced_threads();
            active.sync();
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
            active.sync();
        }
        ...
    }
    ```
