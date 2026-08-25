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
