---
type: API
title: asc_dump
description: 将对应内存上的数据打印出来，同时支持打印自定义的附加信息（仅支持uint32_t类型的信息），比如打印当前行号等。使用该接口需要包含"utils/debug/asc_dump.h"头文件。该功能主要用于调试和性能分析，通常在调测阶段使用，会对算子性能产生一定影响，生产环境可以通过设置ASCENDC_DUMP=0的方式关闭。
tags: [task.lookup, topic.programming_model]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/tuning_interface/asc_dump.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# asc_dump

将对应内存上的数据打印出来，同时支持打印自定义的附加信息（仅支持uint32_t类型的信息），比如打印当前行号等。

使用该接口需要包含"utils/debug/asc_dump.h"头文件。

> [!CAUTION]注意
>该功能主要用于调试和性能分析，通常在调测阶段使用，会对算子性能产生一定影响，生产环境可以通过设置ASCENDC_DUMP=0的方式关闭。
>默认情况下，该功能开启。

函数原型：template<typename T>；__aicore__ static __attribute__((noinline)) void asc_dump_gm(__gm__ T* input, uint32_t desc, uint32_t dump_size)；template<typename T> 等28种重载

参数：T（输入）：待dump的数据类型。；U（输入）：待dump的寄存器数据类型。；input（输入）：所需打印的内存块的起始地址。；desc（输入）：自定义信息。uint32_t类型，支持的数据范围是[0, 2^32 - 1]。；dump_size（输入）：所需要打印的元素数量。

返回值：无

平台支持：Ascend 950PR/950DT、Atlas A3 训练/推理、Atlas A2 训练/推理系列支持，其他产品不支持。
约束：-   针对Ascend 950PR/Ascend 950DT，在使用该接口打印L1 Buffer、BiasTable Buffer或Fixpipe Buffer数据时，HDK版本需要至少升级到25.7.0以上。

<!-- cannbot:related:start -->
## 相关

- [关闭ASCENDC_DUMP说明](../../simd_api/basic_api/debug_interface/disable_ascendc_dump.md)（`same_topic`）：关闭方式：在编译选项中不定义 ASCENDC_DUMP 宏或将其设为 0。；生产环境可以通过设置ASCENDC_DUMP=0的方式关闭。；两卡描述同一 asc_dump 调试能力的生产关闭开关，一端是开关说明，一端是被控制接口的运行边界。
<!-- cannbot:related:end -->
