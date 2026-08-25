---
type: API
title: TraceStart
description: SIMD性能仿真时对算子运行阶段进行起始位置打点，与TraceStop配套使用，用于分析流水图。
tags: [task.lookup, topic.implementation.api_layer.utils_api]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/tuning_interface/TRACE_START.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# TRACE_START

SIMD场景下，通过仿真器进行算子性能仿真时，可对算子任意运行阶段打点，从而分析不同指令的流水图，以便进一步性能调优。

用于表示起始位置打点，一般与TRACE_STOP配套使用。

> [!CAUTION]注意
>该功能主要用于调试和性能分析，开启后会对算子性能产生一定影响，通常在调测阶段使用，生产环境建议关闭。
>默认情况下，该功能关闭，开发者可以按需通过如下方式开启打点功能。
>修改Kernel直调工程cmake目录下的npu_lib.cmake文件，在ascendc_compile_definitions命令中增加-DASCENDC_TRACE_ON编译选项，来开启打点功能。示例如下：
>

参数：apid（输入）：当前预留了十个用户自定义的类型：<br>0x0：USER_DEFINE_0<br>0x1：USER_DEFINE_1<br>0x2：USER_DEFINE_2<br>0x3：USER_DEFINE_3<br>0x4：USER_DEFINE_4<br>0x5：USER_DEFINE_5<br>0x6：USER_DEFINE_6<br>0x7：USER_DEFINE_7<br>0x8：USER_DEFINE_8<br>0x9：USER_DEFINE_9；pipe（输入）：指定打点所在的pipeline类型，取值请参考[硬件流水类型](../../simd_api/basic_api/sync_control/intra_core_sync/intra_core_sync_overview.md#zh-cn_topic_0000002542725361_section1272612276459)。

返回值：无

平台支持：Ascend 950PR/950DT、Atlas A3 训练/推理、Atlas A2 训练/推理系列支持，其他产品不支持。
约束：-   TRACE_START/TRACE_STOP需配套使用，若Trace图上未显示打点，则说明两者没有配对。
-   不支持跨核使用，例如TRACE_START在AI Cube打点，则TRACE_STOP打点也需要在AI Cube上，不能在AI Vector上。
-   宏支持所有的产品型号，但实际调用时需与调测工具支持的型号保持一致。

<!-- cannbot:related:start -->
## 相关

- [TraceStop](trace_stop.md)（`same_topic`）：TraceStop 与《TraceStart》的衔接是：TraceStop 必须与同 apid、pipe、core 上的 TraceStart 成对出现；TraceStart 是完成该闭合区间不可替代的另一端。
<!-- cannbot:related:end -->
