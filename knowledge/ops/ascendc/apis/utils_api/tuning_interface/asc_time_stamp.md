---
type: API
title: AscTimeStamp
description: SIMD场景下提供时间戳打点功能，用于在算子Kernel代码中标记关键执行点，便于调试和性能分析。
tags: [task.lookup, topic.programming_model]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/tuning_interface/asc_time_stamp.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# asc_time_stamp

SIMD场景下，提供时间戳打点功能，用于在算子Kernel代码中标记关键执行点。调用后会打印如下信息：

-   descId：用户自定义标识符，用于区分不同打点位置。
-   rsv：保留值，默认为0，无需关注。
-   timeStamp：当前系统cycle数，用于计算时间差，时间换算规则可参考GetSystemCycle(ISASI)。
-   pcPtr：pc指针数值，若无特殊需求，用户无需关注。
-   entry：算子开始执行的cycle数，若无特殊需求，用户无需关注。

打印示例如下：

> [!CAUTION]注意
>该功能主要用于调试和性能分析，开启后会对算子性能产生一定影响，生产环境建议关闭。
>默认情况下，该功能关闭，开发者可以按需通过增加-DASCENDC_TIME_STAMP_ON编译选项的方式，开启打点功能。

函数原型：__aicore__ static __attribute__((noinline)) void asc_time_stamp(uint32_t desc_id)

参数：desc_id（输入）：用户自定义标识符（自定义数字），用于区分不同打点位置。<br> 注意： <br>[0, 0xffff]是预留给Ascend C内部各个模块使用的id值，用户自定义的desc_id建议使用大于0xffff的数值。

返回值：无

平台支持：Ascend 950PR/950DT、Atlas A3 训练/推理、Atlas A2 训练/推理系列支持，其他产品不支持。
约束：-   该功能仅用于NPU上板调试。
-   暂不支持算子入图场景的打印。

-   单次调用本接口打印的数据总量不可超过1MB（还包括少量框架需要的头尾信息，通常可忽略）。使用时应注意，如果超出这个限制，则数据不会被打印。在使用自定义算子工程进行工程化算子开发时，一个算子所有使用Dump功能的接口在每个核上Dump的数据总量不可超过1MB。请开发者自行控制待打印的内容数据量，超出则不会打印。

<!-- cannbot:related:start -->
## 相关

- [AscGetSystemCycle](../../simd_api/c_api/sys_var/asc_get_system_cycle.md)（`related`）：“AscGetSystemCycle”处理读取当前系统cycle计数器，用于性能统计与耗时测量。；“AscTimeStamp”明确SIMD场景下提供时间戳打点功能，用于在算子Kernel代码中标记关键执行点，便于调试和性能分析。。实质衔接：AscGetSystemCycle 提供原始 cycle；GetSystemCycle 是同义层接口，PrintTimeStamp/AscTimeStamp 是直接消费该计数器的打点能力。
- [Clock](clock.md)（`related`）：Clock 返回从程序启动到当前时刻的周期数，可与 AscTimeStamp 的流水打点按是否需要直接取值或离线分析选型。
- [PrintTimeStamp](../../simd_api/basic_api/debug_interface/onboard_print/print_time_stamp.md)（`related`）：AscTimeStamp 记录关键点时间戳用于分析，PrintTimeStamp 进一步把当前 cycle 打印出来，适合现场核对打点顺序。
- [asc_mark_stamp](asc_mark_stamp.md)（`related`）：asc_time_stamp 记录时间而 mark_stamp 标注路径位置，二者组合可定位热点并估计阶段耗时。
<!-- cannbot:related:end -->
