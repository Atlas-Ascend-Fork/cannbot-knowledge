---
type: API
title: tiled_partition
description: 将线程组划分为多个更小、固定大小的子组，提供模板和非模板版本，分别用于编译时和运行时确定划分大小，模板版本支持跨Warp。
tags:
- task.lookup
- topic.implementation.api_layer.simt_api
- topic.programming_model.cooperative_groups
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/cooperative_groups/tiled_partition.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- '950'
source_headers:
- include/simt_api/cooperative_groups.h
---

# tiled_partition

## 功能说明

`tiled_partition` API用于将一个线程组划分为多个更小、固定大小的子组，以便线程在以更精细的粒度上进行协作。提供模板和非模板两个版本的接口，分别用于编译时确定划分大小以及运行时确定划分大小的场景。模板版本支持创建跨Warp的`thread_block_tile`。

## 函数原型

```cpp
template <unsigned int Size, typename ParentT>
thread_block_tile<Size, ParentT> tiled_partition(const ParentT& g)
```

```cpp
thread_group tiled_partition(const thread_group& parent, unsigned int tilesz)
```

```cpp
thread_group tiled_partition(const thread_block& parent, unsigned int tilesz)
```

```cpp
coalesced_group tiled_partition(const coalesced_group& parent, unsigned int tilesz)
```

## 参数说明

**表1**  模板版本参数说明

| 参数名 | 输入/输出 | 描述 |
| --- | --- | --- |
| g | 输入 | 被划分的父组，类型只能是`thread_block`或`thread_block_tile`。 |
| Size | 输入 | 模板参数，指定划分出的`thread_block_tile`组大小。 |

**表2**  非模板版本参数说明

| 参数名 | 输入/输出 | 描述 |
| --- | --- | --- |
| parent | 输入 | 被划分的父组，类型只能是`thread_block`或`coalesced_group`。 |
| tilesz | 输入 | 指定划分出的子组大小。 |

## 返回值说明

返回划分出的子组对象。

## 约束说明

- 模板版本中，`Size`必须是$2^n$，当前可选值范围：1、2、4、8、16、32、64、128、256、512、1024、2048。
- 非模板版本仅支持创建`tilesz <= 32`的子组，且`tilesz`必须是2的幂（即取值范围为1、2、4、8、16、32）。
- 当要创建跨Warp的`thread_block_tile`时，用户需创建[block_tile_memory](thread_block/thread_block_constructor.md#block_tile_memory说明)作为临时存储，并通过带`scratch`参数的`this_thread_block`创建父`thread_block`。传入的`block_tile_memory`对象必须位于Global Memory或Unified Buffer（UB），不能传入栈空间中创建的对象。使用位于UB的对象性能优于位于Global Memory的。
- 对于模板版本的接口，父组中的线程数必须能被`Size`整除。并且如果父组是`thread_block_tile`，则`Size`必须小于父组大小。

## 调用示例

- SIMT编程场景：

    ```cpp
    using namespace cooperative_groups;
    __global__ void simt_kernel(...)
    {
        ...
        // 无需使用跨warp的thread_block_tile
        thread_block block = this_thread_block();
        auto tile4 = tiled_partition<4>(block);

        // 需要使用跨warp的thread_block_tile
        __ubuf__ block_tile_memory<1024> scratch;
        thread_block block_with_memory = this_thread_block(scratch);
        auto tile64 = tiled_partition<64>(block_with_memory);
        ...
    }
    ```

- SIMD与SIMT混合编程场景：

    ```cpp
    using namespace cooperative_groups;
    __simt_vf__ inline void simt_kernel(...)
    {
        ...
        // 无需使用跨warp的thread_block_tile
        thread_block block = this_thread_block();
        auto tile4 = tiled_partition<4>(block);

        // 需要使用跨warp的thread_block_tile
        __ubuf__ block_tile_memory<1024> scratch;
        thread_block block_with_memory = this_thread_block(scratch);
        auto tile64 = tiled_partition<64>(block_with_memory);
        ...
    }
    ```


<!-- cannbot:related:start -->
## 相关

- [MetaGroupRank](thread_block_tile/meta_group_rank.md)（`related`）：获取当前线程所在的组在从父组划分出的子组集合中的排名，排名从0开始。；返回值：返回划分出的子组对象。tiled_partition 生产子组集合，MetaGroupRank 在该集合中解释当前组序号，形成直接对象生产与查询链。
- [ShflUp](thread_block_tile/shfl_up.md)（`related`）：获取thread_block_tile组内当前线程向前偏移delta的线程的数据。；tiled_partition API用于将一个线程组划分为多个更小、固定大小的子组，以便线程在以更精细的粒度上进行协作。。tiled_partition 先创建固定大小的 thread_block_tile，shfl_up 再在该组内按 delta 读取前方线程数据，形成分组到组内通信的使用链。
- [thread_block_tile构造函数](thread_block_tile/thread_block_tile_constructor.md)（`related`）：tiled_partition API用于将一个线程组划分为多个更小、固定大小的子组，以便线程在以更精细的粒度上进行协作。；thread_block_tile不提供默认构造函数，可通过tiled_partition接口从另一个协作组中划分得到。前者定义划分操作，后者把该操作确定为 thread_block_tile 的构造入口。
<!-- cannbot:related:end -->
