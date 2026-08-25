---
type: API
title: Assert
description: CPU/NPU域assert断言接口，条件判断不为真时输出断言条件并格式化打印，主要用于调试阶段。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.debugging]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/debug_interface/exception_detection/assert.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# Assert

CPU/NPU 域 assert 断言接口。条件不为真时输出断言条件并格式化打印，NPU 模式下触发 Trap 中断。参数 condition 为判断条件，format 为格式化字符串。仅调试阶段使用。支持 950/a2/a3。

<!-- cannbot:related:start -->
## 相关

- [Trap](trap.md)（`related`）：NPU 模式下 Assert 条件失败最终触发 Trap 中断，Trap 是不需要格式化条件输出时的直接终止原语。
- [assert（AI CPU API）](../../../../ai_cpu_api/assert.md)（`related`）：两卡都以条件失败触发设备侧诊断，但目标接口运行在 SIMD/SIMT AI Core 域；对照可防止把 AI CPU 断言的链接和调用规则套到 AI Core。
- [关闭ASCENDC_DUMP说明](../disable_ascendc_dump.md)（`related`）：关闭ASCENDC_DUMP说明 与《Assert》的实质衔接是：ASCENDC_DUMP 宏直接控制 assert、dump、上板打印和异常检测类调试接口；这些接口只应在调测期开启，生产关闭以避免性能影响。
- [异常检测](exception_detection.md)（`related`）：《异常检测》说明异常检测接口集，包含 ascendc_assert、assert、Trap、CheckLocalMemoryIA(ISASI) 等接口。；《Assert》说明CPU/NPU域assert断言接口，条件判断不为真时输出断言条件并格式化打印，主要用于调试阶段。。二者在异常检测索引把AscendcAssert、Assert、Trap和CheckLocalMemoryIA组成设备侧诊断入口上存在可执行的直接衔接。
- [AscendcAssert](ascendc_assert.md)（`same_topic`）：《AscendcAssert》说明CPU/NPU域断言接口，当断言条件不满足时输出断言信息并格式化打印，主要用于调试阶段。；《Assert》说明CPU/NPU域assert断言接口，条件判断不为真时输出断言条件并格式化打印，主要用于调试阶段。。二者在AscendcAssert属于异常检测工具链，与Assert、Trap和本地内存检查共同完成设备侧失败定位上存在可执行的直接衔接。
- [Assert](../../../../utils_api/tuning_interface/assert.md)（`same_topic`）：Assert说明CPU/NPU域assert断言接口，条件判断不为真时输出断言条件并格式化打印，主要用于调试阶段。
- [CheckLocalMemoryIA](check_local_memory_ia_isasi.md)（`same_topic`）：CheckLocalMemoryIA 与《Assert》的实质衔接是：CheckLocalMemoryIA 通过保留的 UB 地址范围触发异常，需结合 LocalMemAllocator、地址空间转换与 ASCENDC_DUMP 调试开关定位本地内存越界。
<!-- cannbot:related:end -->
