---
type: API
title: DumpAccChkPoint
description: 打印指定Tensor内容并支持自定义标签，区别于DumpTensor，支持指定偏移位置开始打印Tensor数据。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.debugging]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/debug_interface/onboard_print/DumpAccChkPoint.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# DumpAccChkPoint

打印指定 Tensor 内容并支持自定义标签。区别于 DumpTensor，支持指定偏移位置开始打印。参数含 Tensor、偏移量、打印元素数和自定义标签字符串。需开启 ASCENDC_DUMP 宏。支持 950/a2/a3。

<!-- cannbot:related:start -->
## 相关

- [NPU域上板调试（功能调试）](../../../../../guides/programming_guide/debug_and_tuning/functional_debug/npu_board_debug.md)（`explains`）：《NPU域上板调试（功能调试）》处理“NPU域上板调试手段主要包含上板数据打印、msSanitizer内存异常检测和msDebug单步调试等功能，数据打印包括printf、DumpTensor两种方式，其中，DumpTensor是SIMD编程独有功能，用于打印指定Tensor的数据。”。《DumpAccChkPoint》提供“打印指定Tensor内容并支持自定义标签，区别于DumpTensor，支持指定偏移位置开始打印Tensor数据。”，其具体合同或探针直接接入NPU 上板打印、异常定位、Tiling 调试、精度对比和离线解析流程。
- [DumpTensor](dump_tensor.md)（`related`）：《DumpTensor》说明打印Tensor内容并支持自定义标签，可选传入Shape信息按指定维度排列展示数据。；《DumpAccChkPoint》说明打印指定Tensor内容并支持自定义标签，区别于DumpTensor，支持指定偏移位置开始打印Tensor数据。。二者在DumpTensor/asc_dump、checkpoint、开关和上板调试工具构成设备张量观测链；VF和精度卡给出不可用PRINTF时的替代证据路径上存在可执行的直接衔接。
- [asc_dump](../../../../utils_api/tuning_interface/asc_dump.md)（`related`）：DumpAccChkPoint 与《asc_dump》的实质衔接是：DumpAccChkPoint 与 DumpTensor 都受 ASCENDC_DUMP 控制，前者额外支持 offset；上板打印与 NPU 域调试指南给出启用位置，asc_dump 是 C 接口层对应的内存打印能力。
- [上板打印](onboard_print.md)（`related`）：DumpAccChkPoint 记录计算检查点，适合在无法完整打印大 Tensor 时定位流水阶段。
- [关闭ASCENDC_DUMP说明](../disable_ascendc_dump.md)（`related`）：关闭ASCENDC_DUMP说明 与《DumpAccChkPoint》的实质衔接是：ASCENDC_DUMP 宏直接控制 assert、dump、上板打印和异常检测类调试接口；这些接口只应在调测期开启，生产关闭以避免性能影响。
<!-- cannbot:related:end -->
