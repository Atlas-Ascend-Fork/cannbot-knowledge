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
