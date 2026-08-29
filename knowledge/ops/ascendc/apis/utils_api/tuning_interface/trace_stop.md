---
type: API
title: TraceStop
description: SIMD性能仿真时对算子运行阶段进行终止位置打点，与TraceStart配套使用，用于分析流水图。
tags: [task.lookup, topic.implementation.api_layer.utils_api]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/tuning_interface/TRACE_STOP.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# TRACE_STOP

SIMD场景下，通过仿真器进行算子性能仿真时，可对算子任意运行阶段打点，从而分析不同指令的流水图，以便进一步性能调优。

用于表示终止位置打点，一般与TRACE_START配套使用。

> [!CAUTION]注意
>该功能主要用于调试和性能分析，开启后会对算子性能产生一定影响，通常在调测阶段使用，生产环境建议关闭。
>默认情况下，该功能关闭，开发者可以按需通过如下方式开启打点功能。
>修改Kernel直调工程cmake目录下的npu_lib.cmake文件，在ascendc_compile_definitions命令中增加-DASCENDC_TRACE_ON编译选项，来开启打点功能。示例如下：
>

参数：apid（输入）：取值需与[TRACE_START](trace_start.md)参数取值保持一致，否则影响打点结果。；pipe（输入）：取值需与[TRACE_START](trace_start.md)的pipe参数取值保持一致，pipe取值请参考[硬件流水类型](../../simd_api/basic_api/sync_control/intra_core_sync/intra_core_sync_overview.md#zh-cn_topic_0000002542725361_section1272612276459)，否则影响打点结果。

返回值：无

平台支持：Ascend 950PR/950DT、Atlas A3 训练/推理、Atlas A2 训练/推理系列支持，其他产品不支持。
约束：-   TRACE_START/TRACE_STOP需配套使用，若Trace图上未显示打点，则说明两者没有配对。
-   不支持跨核使用，例如TRACE_START在AI Cube打点，则TRACE_STOP打点也需要在AI Cube上，不能在AI Vector上。
-   宏支持所有的产品型号，但实际调用时需与调测工具支持的型号保持一致。

<!-- cannbot:related:start -->
## 相关

- [TraceStart](trace_start.md)（`related`）：“用于表示起始位置打点，一般与TRACE_STOP配套使用。”给出焦点端事实；“用于表示终止位置打点，一般与TRACE_START配套使用。”给出候选端事实。两端明确互为配套的起止打点接口，联合使用才能形成完整的调优测量区间。
<!-- cannbot:related:end -->
