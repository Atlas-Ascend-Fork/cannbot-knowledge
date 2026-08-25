---
type: API
title: PrintTimeStamp
description: 提供时间戳打点功能，用于在算子Kernel代码中标记关键执行点并打印当前系统cycle数。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.debugging]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/debug_interface/onboard_print/PrintTimeStamp.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# PrintTimeStamp

提供时间戳打点功能，用于在算子Kernel代码中标记关键执行点并打印当前系统cycle数。

SIMD场景下，提供时间戳打点功能，用于在算子Kernel代码中标记关键执行点。调用后会打印如下信息： - descId：用户自定义标识符，用于区分不同打点位置。 - rsv：保留值，默认为0，无需关注。 - timeStamp：当前系统cycle数，用于计算时间差，时间换算规则可参考GetSystemCycle(ISASI)。 - pcPtr：pc指针数值，若无特殊需求，用户无需关注。 - entry：算子开始执行的cycle数，若无特殊需求，用户无需关注。 打印示例如下： > [!CAUTION]注意 >该功能主要用于调试和性能分析，开启后会对算子性能产生一定影响，生产环境建议关闭。 >默认情况下，该功能关闭，开发者可以按需通过增加-DASCENDC_TIME_STAMP_ON编译选项的方式，开启打点功能。

本接口组包含 asc_time_stamp，辅助接口包括 GetSystemCycle(ISASI)。

本接口属于调试接口，用于算子开发过程中的调试和诊断。

约束：该功能仅用于NPU上板调试。；暂不支持算子入图场景的打印。；单次调用本接口打印的数据总量不可超过1MB（还包括少量框架需要的头尾信息，通常可忽略）。使用时应注意，如果超出这个限制，则数据不会被打印。在使用自定义算子工程进行工程化算子开发时，一个算子所有使用Dump功能的接口在每个核上Dump的数据总量不可超过1MB。请开发者自行控制待打印的内容数据量，超出则不会打印。

支持的硬件型号：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。

<!-- cannbot:related:start -->
## 相关

- [AscGetSystemCycle](../../../c_api/sys_var/asc_get_system_cycle.md)（`related`）：“AscGetSystemCycle”处理读取当前系统cycle计数器，用于性能统计与耗时测量。；“PrintTimeStamp”明确提供时间戳打点功能，用于在算子Kernel代码中标记关键执行点并打印当前系统cycle数。。实质衔接：AscGetSystemCycle 提供原始 cycle；GetSystemCycle 是同义层接口，PrintTimeStamp/AscTimeStamp 是直接消费该计数器的打点能力。
- [AscTimeStamp](../../../../utils_api/tuning_interface/asc_time_stamp.md)（`related`）：AscTimeStamp 记录关键点时间戳用于分析，PrintTimeStamp 进一步把当前 cycle 打印出来，适合现场核对打点顺序。
- [GetSystemCycle](../../tool_interface/system_resources_and_variables/get_system_cycle_isasi.md)（`related`）：“PrintTimeStamp”处理提供时间戳打点功能，用于在算子Kernel代码中标记关键执行点并打印当前系统cycle数。；“GetSystemCycle”明确获取系统计数器当前的cycle值，通过前后差值可计算代码段执行时间。。实质衔接：PrintTimeStamp 以系统 cycle 为时间基准；AscTimeStamp 是同一打点能力，MarkStamp 是流水标记替代，GetSystemCycle 提供换算基准。
- [MarkStamp](../performance_stats/mark_stamp.md)（`related`）：“PrintTimeStamp”处理提供时间戳打点功能，用于在算子Kernel代码中标记关键执行点并打印当前系统cycle数。；“MarkStamp”明确推荐使用asc_mark_stamp接口进行特定位置的标记，该接口同时适用于C语言和C++语言编程。 用户通过调用接口，用于在算子执行过程中标记特定位置，便于后期通过流水图分析代码执行路径与性能热点。。实质衔接：PrintTimeStamp 以系统 cycle 为时间基准；AscTimeStamp 是同一打点能力，MarkStamp 是流水标记替代，GetSystemCycle 提供换算基准。
- [上板打印](onboard_print.md)（`related`）：PrintTimeStamp 用于输出时间戳，和数据打印组合可定位性能或执行顺序问题。
<!-- cannbot:related:end -->
