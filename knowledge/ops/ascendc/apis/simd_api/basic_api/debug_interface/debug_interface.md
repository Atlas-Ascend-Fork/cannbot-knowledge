---
type: API
title: 调试接口
description: AscendC 调试接口总览，涵盖上板打印、异常检测、CPU 孪生调试、性能统计及 ASCENDC_DUMP 控制说明。
tags: [task.lookup, topic.implementation.debugging]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/debug_interface/debug_interface.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 调试接口

AscendC 调试接口总览，涵盖上板打印（NPU 运行时输出调试信息）、异常检测（断言与 trap）、CPU 孪生调试（CPU 侧模拟核函数）、性能统计（算子耗时与流水分析）四类调试能力，以及关闭 ASCENDC_DUMP 的说明。开发者可按调试阶段选择对应工具：CPU 侧验证逻辑，上板侧定位真实硬件问题。

<!-- cannbot:related:start -->
## 相关

- [NPU域上板调试（功能调试）](../../../../guides/programming_guide/debug_and_tuning/functional_debug/npu_board_debug.md)（`explains`）：《NPU域上板调试（功能调试）》处理“NPU域上板调试手段主要包含上板数据打印、msSanitizer内存异常检测和msDebug单步调试等功能，数据打印包括printf、DumpTensor两种方式，其中，DumpTensor是SIMD编程独有功能，用于打印指定Tensor的数据。”。《调试接口》提供“AscendC 调试接口总览，涵盖上板打印、异常检测、CPU 孪生调试、性能统计及 ASCENDC_DUMP 控制说明。”，其具体合同或探针直接接入NPU 上板打印、异常定位、Tiling 调试、精度对比和离线解析流程。
- [AscendcAssert](exception_detection/ascendc_assert.md)（`related`）：《AscendcAssert》说明CPU/NPU域断言接口，当断言条件不满足时输出断言信息并格式化打印，主要用于调试阶段。；《调试接口》说明AscendC 调试接口总览，涵盖上板打印、异常检测、CPU 孪生调试、性能统计及 ASCENDC_DUMP 控制说明。。二者在AscendcAssert属于异常检测工具链，与Assert、Trap和本地内存检查共同完成设备侧失败定位上存在可执行的直接衔接。
- [DumpTensor](onboard_print/dump_tensor.md)（`related`）：《DumpTensor》说明打印Tensor内容并支持自定义标签，可选传入Shape信息按指定维度排列展示数据。；《调试接口》说明AscendC 调试接口总览，涵盖上板打印、异常检测、CPU 孪生调试、性能统计及 ASCENDC_DUMP 控制说明。。二者在DumpTensor/asc_dump、checkpoint、开关和上板调试工具构成设备张量观测链；VF和精度卡给出不可用PRINTF时的替代证据路径上存在可执行的直接衔接。
- [异常检测](exception_detection/exception_detection.md)（`related`）：《异常检测》说明异常检测接口集，包含 ascendc_assert、assert、Trap、CheckLocalMemoryIA(ISASI) 等接口。；《调试接口》说明AscendC 调试接口总览，涵盖上板打印、异常检测、CPU 孪生调试、性能统计及 ASCENDC_DUMP 控制说明。。二者在异常检测索引把AscendcAssert、Assert、Trap和CheckLocalMemoryIA组成设备侧诊断入口上存在可执行的直接衔接。
- [关闭ASCENDC_DUMP说明](disable_ascendc_dump.md)（`same_topic`）：关闭ASCENDC_DUMP说明 与《调试接口》的实质衔接是：ASCENDC_DUMP 宏直接控制 assert、dump、上板打印和异常检测类调试接口；这些接口只应在调测期开启，生产关闭以避免性能影响。
<!-- cannbot:related:end -->
