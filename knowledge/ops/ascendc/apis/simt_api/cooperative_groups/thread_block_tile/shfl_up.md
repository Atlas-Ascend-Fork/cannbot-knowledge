---
type: API
title: ShflUp
description: 获取thread_block_tile组内当前线程向前偏移delta的线程的数据。
tags:
- task.lookup
- topic.implementation.api_layer.simt_api
- topic.programming_model.cooperative_groups
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/cooperative_groups/thread_block_tile/shfl_up.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- '950'
---

# shfl_up

## 功能说明

获取`thread_block_tile`组内当前线程向前偏移`delta`的线程的数据。

## 函数原型

```cpp
template <typename T>
T shfl_up(T var, unsigned int delta) const
```

## 参数说明

**表1**  参数说明

| 参数名 | 输入/输出 | 描述 |
| --- | --- | --- |
| var | 输入 | 线程用于交换的输入操作数。支持的数据类型为：half、int32_t、uint32_t、float、half2、int64_t、uint64_t、bfloat16_t、bfloat16x2_t。 |
| delta | 输入 | 期望获取的`var`值所在线程在组内相对当前线程的向前偏移值。 |

## 返回值说明

协作组内当前线程向前偏移`delta`的线程输入的`var`值。若偏移后超出组范围，返回当前线程输入的`var`值。

## 约束说明

仅支持`thread_block_tile`的模板参数`Size`小于等于32且为2的幂（1、2、4、8、16、32）的场景，即仅支持单Warp内线程子组。

## 调用示例

以4个线程为一组划分线程块，获取协作组内当前线程向前偏移`delta`的线程输入的`var`值。

**图1**  shfl_up接口返回结果示意图  
![](https://raw.gitcode.com/cann/asc-devkit/raw/885973fe9fd42a600e3551af9bc11a279e6f183b/docs/zh/api/figures/thread_block_tile_shfl_up.png "thread_block_tile_shfl_up")

- SIMT编程场景：

    ```cpp
    using namespace cooperative_groups;
    __global__ void simt_kernel(...)
    {
        ...
        thread_block block = this_thread_block();
        auto tile4 = tiled_partition<4>(block);
        uint32_t result = tile4.shfl_up(threadIdx.x + 100, 2);
        ...
    }
    ```

- SIMD与SIMT混合编程场景：

    ```cpp
    using namespace cooperative_groups;
    __simt_vf__ inline void simt_kernel(...)
    {
        ...
        thread_block block = this_thread_block();
        auto tile4 = tiled_partition<4>(block);
        uint32_t result = tile4.shfl_up(threadIdx.x + 100, 2);
        ...
    }
    ```


<!-- cannbot:related:start -->
## 相关

- [tiled_partition](../tiled_partition.md)（`related`）：获取thread_block_tile组内当前线程向前偏移delta的线程的数据。；tiled_partition API用于将一个线程组划分为多个更小、固定大小的子组，以便线程在以更精细的粒度上进行协作。。tiled_partition 先创建固定大小的 thread_block_tile，shfl_up 再在该组内按 delta 读取前方线程数据，形成分组到组内通信的使用链。
<!-- cannbot:related:end -->
