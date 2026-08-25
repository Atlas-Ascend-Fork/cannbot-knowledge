---
type: API
title: 关闭ASCENDC_DUMP说明
description: 调试接口（如本章的上板打印、异常检测接口）开启后会对算子性能产生一定影响，通常在调测阶段使用，生产环境建议关闭。ASCENDC_DUMP宏定义是控制调试接口打印的开关。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.debugging]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/debug_interface/disable_ascendc_dump.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 关闭ASCENDC_DUMP说明

ASCENDC_DUMP 宏定义控制调试接口（上板打印、异常检测等）的打印开关。调测阶段开启，生产环境建议关闭以避免性能影响。关闭方式：在编译选项中不定义 ASCENDC_DUMP 宏或将其设为 0。

<!-- cannbot:related:start -->
## 相关

- [AscendcAssert](exception_detection/ascendc_assert.md)（`related`）：《AscendcAssert》说明CPU/NPU域断言接口，当断言条件不满足时输出断言信息并格式化打印，主要用于调试阶段。；《关闭ASCENDC_DUMP说明》说明调试接口（如本章的上板打印、异常检测接口）开启后会对算子性能产生一定影响，通常在调测阶段使用，生产环境建议关闭。ASCENDC_DUMP宏定义是控制调试接口打印的开关。。二者在AscendcAssert属于异常检测工具链，与Assert、Trap和本地内存检查共同完成设备侧失败定位上存在可执行的直接衔接。
- [Assert](exception_detection/assert.md)（`related`）：关闭ASCENDC_DUMP说明 与《Assert》的实质衔接是：ASCENDC_DUMP 宏直接控制 assert、dump、上板打印和异常检测类调试接口；这些接口只应在调测期开启，生产关闭以避免性能影响。
- [CheckLocalMemoryIA](exception_detection/check_local_memory_ia_isasi.md)（`related`）：CheckLocalMemoryIA 与《关闭ASCENDC_DUMP说明》的实质衔接是：CheckLocalMemoryIA 通过保留的 UB 地址范围触发异常，需结合 LocalMemAllocator、地址空间转换与 ASCENDC_DUMP 调试开关定位本地内存越界。
- [DumpAccChkPoint](onboard_print/dump_acc_chk_point.md)（`related`）：关闭ASCENDC_DUMP说明 与《DumpAccChkPoint》的实质衔接是：ASCENDC_DUMP 宏直接控制 assert、dump、上板打印和异常检测类调试接口；这些接口只应在调测期开启，生产关闭以避免性能影响。
- [DumpTensor](onboard_print/dump_tensor.md)（`related`）：《DumpTensor》说明打印Tensor内容并支持自定义标签，可选传入Shape信息按指定维度排列展示数据。；《关闭ASCENDC_DUMP说明》说明调试接口（如本章的上板打印、异常检测接口）开启后会对算子性能产生一定影响，通常在调测阶段使用，生产环境建议关闭。ASCENDC_DUMP宏定义是控制调试接口打印的开关。。二者在DumpTensor/asc_dump、checkpoint、开关和上板调试工具构成设备张量观测链；VF和精度卡给出不可用PRINTF时的替代证据路径上存在可执行的直接衔接。
- [Trap](exception_detection/trap.md)（`related`）：关闭ASCENDC_DUMP说明 与《Trap》的实质衔接是：ASCENDC_DUMP 宏直接控制 assert、dump、上板打印和异常检测类调试接口；这些接口只应在调测期开启，生产关闭以避免性能影响。
- [asc_dump](../../../utils_api/tuning_interface/asc_dump.md)（`related`）：“asc_dump”定义：将对应内存上的数据打印出来，同时支持打印自定义的附加信息（仅支持uint32_t类型的信息），比如打印当前行号等。使用该接口需要包含"utils/debug/asc_dump.h"头文件。该功能主要用于调试和性能分析，通常在调测阶段使用，会对算子性能产生一定影响，生产环境可以通过设置ASCENDC_DUMP=0的方式关闭。；“关闭ASCENDC_DUMP说明”定义：调试接口（如本章的上板打印、异常检测接口）开启后会对算子性能产生一定影响，通常在调测阶段使用，生产环境建议关闭。ASCENDC_DUMP宏定义是控制调试接口打印的开关。。实质衔接：asc_dump 用于调试期查看任意内存并带附加信息；DumpTensor 是张量级替代，生产环境需通过 ASCENDC_DUMP 关闭以免影响性能。
- [上板打印](onboard_print/onboard_print.md)（`related`）：关闭ASCENDC_DUMP说明 与《上板打印》的实质衔接是：ASCENDC_DUMP 宏直接控制 assert、dump、上板打印和异常检测类调试接口；这些接口只应在调测期开启，生产关闭以避免性能影响。
- [异常检测](exception_detection/exception_detection.md)（`related`）：《异常检测》说明异常检测接口集，包含 ascendc_assert、assert、Trap、CheckLocalMemoryIA(ISASI) 等接口。；《关闭ASCENDC_DUMP说明》说明调试接口（如本章的上板打印、异常检测接口）开启后会对算子性能产生一定影响，通常在调测阶段使用，生产环境建议关闭。ASCENDC_DUMP宏定义是控制调试接口打印的开关。。二者在异常检测索引把AscendcAssert、Assert、Trap和CheckLocalMemoryIA组成设备侧诊断入口上存在可执行的直接衔接。
- [调试接口](debug_interface.md)（`same_topic`）：关闭ASCENDC_DUMP说明 与《调试接口》的实质衔接是：ASCENDC_DUMP 宏直接控制 assert、dump、上板打印和异常检测类调试接口；这些接口只应在调测期开启，生产关闭以避免性能影响。
<!-- cannbot:related:end -->
