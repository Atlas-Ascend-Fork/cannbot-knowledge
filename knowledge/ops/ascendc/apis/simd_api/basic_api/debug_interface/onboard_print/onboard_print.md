---
type: API
title: 上板打印
description: 上板打印接口集，包含 DumpTensor、DumpAccChkPoint、PrintTimeStamp 等调试输出接口。
tags: [task.lookup, topic.implementation.debugging]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/debug_interface/onboard_print/onboard_print.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# 上板打印

上板打印接口集，包含 DumpTensor、DumpAccChkPoint、PrintTimeStamp 等调试输出接口。

该接口可以打印Tensor的内容，同时支持打印自定义的标签（仅支持uint32_t数据类型的信息），比如打印当前行号等。 在算子kernel侧实现代码中需要打印Tensor数据的地方，调用DumpTensor接口打印相关内容。样例如下： > [!CAUTION]注意 > 该接口主要用于调试分析，开启后会对算子性能产生一定影响，通常在调试阶段使用，生产环境建议关闭。 > 默认情况下，调用该接口就会打印相关内容，开发者可以参考关闭ASCENDC_DUMP说明，按需关闭该接口功能。 打印示例如下：

本接口组包含 DumpTensor, DumpAccChkPoint, PrintTimeStamp。

本接口属于调试接口，用于算子开发过程中的调试和诊断。

约束：当前支持打印存储位置为Unified Buffer/L1 Buffer/L0C Buffer/Global Memory的Tensor信息。；在Ascend 950PR/Ascend 950DT下新增BiasTable Buffer和Fixpipe Buffer的Tensor数据打印。；针对Ascend 950PR/Ascend 950DT，使用该接口打印L1 Buffer、BiasTable Buffer或Fixpipe Buffer数据时，HDK版本需要至少升级到25.7.0以上。；针对Ascend 950PR/Ascend 950DT，打印Fixpipe Buffer中的Tensor信息场景：

支持的硬件型号：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。

<!-- cannbot:related:start -->
## 相关

- [NPU域上板调试（功能调试）](../../../../../guides/programming_guide/debug_and_tuning/functional_debug/npu_board_debug.md)（`explains`）：《NPU域上板调试（功能调试）》处理“NPU域上板调试手段主要包含上板数据打印、msSanitizer内存异常检测和msDebug单步调试等功能，数据打印包括printf、DumpTensor两种方式，其中，DumpTensor是SIMD编程独有功能，用于打印指定Tensor的数据。”。《上板打印》提供“上板打印接口集，包含 DumpTensor、DumpAccChkPoint、PrintTimeStamp 等调试输出接口。”，其具体合同或探针直接接入NPU 上板打印、异常定位、Tiling 调试、精度对比和离线解析流程。
- [DumpAccChkPoint](dump_acc_chk_point.md)（`related`）：DumpAccChkPoint 记录计算检查点，适合在无法完整打印大 Tensor 时定位流水阶段。
- [DumpTensor](dump_tensor.md)（`related`）：《DumpTensor》说明打印Tensor内容并支持自定义标签，可选传入Shape信息按指定维度排列展示数据。；《上板打印》说明上板打印接口集，包含 DumpTensor、DumpAccChkPoint、PrintTimeStamp 等调试输出接口。。二者在DumpTensor/asc_dump、checkpoint、开关和上板调试工具构成设备张量观测链；VF和精度卡给出不可用PRINTF时的替代证据路径上存在可执行的直接衔接。
- [PrintTimeStamp](print_time_stamp.md)（`related`）：PrintTimeStamp 用于输出时间戳，和数据打印组合可定位性能或执行顺序问题。
- [关闭ASCENDC_DUMP说明](../disable_ascendc_dump.md)（`related`）：关闭ASCENDC_DUMP说明 与《上板打印》的实质衔接是：ASCENDC_DUMP 宏直接控制 assert、dump、上板打印和异常检测类调试接口；这些接口只应在调测期开启，生产关闭以避免性能影响。
<!-- cannbot:related:end -->
