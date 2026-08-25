---
type: API
title: 异常检测
description: 异常检测接口集，包含 ascendc_assert、assert、Trap、CheckLocalMemoryIA(ISASI) 等接口。
tags: [task.lookup, topic.implementation.debugging]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/debug_interface/exception_detection/exception_detection.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 异常检测

AscendC 异常检测接口集合，用于在核函数运行时进行条件检查与异常触发。ascendc_assert、assert 用于条件断言，条件不满足时触发异常；Trap 主动触发 trap 中断；CheckLocalMemoryIA(ISASI) 用于 ISASI 场景下检查 local memory 使用情况。异常检测有助于定位越界、溢出、资源超限等问题。

<!-- cannbot:related:start -->
## 相关

- [Assert](assert.md)（`related`）：《异常检测》说明异常检测接口集，包含 ascendc_assert、assert、Trap、CheckLocalMemoryIA(ISASI) 等接口。；《Assert》说明CPU/NPU域assert断言接口，条件判断不为真时输出断言条件并格式化打印，主要用于调试阶段。。二者在异常检测索引把AscendcAssert、Assert、Trap和CheckLocalMemoryIA组成设备侧诊断入口上存在可执行的直接衔接。
- [CheckLocalMemoryIA](check_local_memory_ia_isasi.md)（`related`）：《异常检测》说明异常检测接口集，包含 ascendc_assert、assert、Trap、CheckLocalMemoryIA(ISASI) 等接口。；《CheckLocalMemoryIA》说明检查设定范围内UB读写行为的调试接口，有设定范围的读写行为会触发EXCEPTION报错。。二者在异常检测索引把AscendcAssert、Assert、Trap和CheckLocalMemoryIA组成设备侧诊断入口上存在可执行的直接衔接。
- [Trap](trap.md)（`related`）：《异常检测》说明异常检测接口集，包含 ascendc_assert、assert、Trap、CheckLocalMemoryIA(ISASI) 等接口。；《Trap》说明Kernel侧调试接口，NPU模式下中断AI Core运行，CPU模式下等同于assert，用于异常场景调试。。二者在异常检测索引把AscendcAssert、Assert、Trap和CheckLocalMemoryIA组成设备侧诊断入口上存在可执行的直接衔接。
- [__trap](../../../../utils_api/tuning_interface/_trap.md)（`related`）：异常检测说明异常检测接口集，包含 ascendc_assert、assert、Trap、CheckLocalMemoryIA(ISASI) 等接口。
- [关闭ASCENDC_DUMP说明](../disable_ascendc_dump.md)（`related`）：《异常检测》说明异常检测接口集，包含 ascendc_assert、assert、Trap、CheckLocalMemoryIA(ISASI) 等接口。；《关闭ASCENDC_DUMP说明》说明调试接口（如本章的上板打印、异常检测接口）开启后会对算子性能产生一定影响，通常在调测阶段使用，生产环境建议关闭。ASCENDC_DUMP宏定义是控制调试接口打印的开关。。二者在异常检测索引把AscendcAssert、Assert、Trap和CheckLocalMemoryIA组成设备侧诊断入口上存在可执行的直接衔接。
- [调试接口](../debug_interface.md)（`related`）：《异常检测》说明异常检测接口集，包含 ascendc_assert、assert、Trap、CheckLocalMemoryIA(ISASI) 等接口。；《调试接口》说明AscendC 调试接口总览，涵盖上板打印、异常检测、CPU 孪生调试、性能统计及 ASCENDC_DUMP 控制说明。。二者在异常检测索引把AscendcAssert、Assert、Trap和CheckLocalMemoryIA组成设备侧诊断入口上存在可执行的直接衔接。
- [AscendcAssert](ascendc_assert.md)（`same_topic`）：《异常检测》说明异常检测接口集，包含 ascendc_assert、assert、Trap、CheckLocalMemoryIA(ISASI) 等接口。；《AscendcAssert》说明CPU/NPU域断言接口，当断言条件不满足时输出断言信息并格式化打印，主要用于调试阶段。。二者在异常检测索引把AscendcAssert、Assert、Trap和CheckLocalMemoryIA组成设备侧诊断入口上存在可执行的直接衔接。
<!-- cannbot:related:end -->
