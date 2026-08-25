---
type: API
title: CheckLocalMemoryIA
description: 检查设定范围内UB读写行为的调试接口，有设定范围的读写行为会触发EXCEPTION报错。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.debugging]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/debug_interface/exception_detection/CheckLocalMemoryIA_ISASI.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# CheckLocalMemoryIA

检查设定范围内 UB 读写行为的调试接口。设定范围内的读写行为会触发 EXCEPTION 报错，用于检测越界访问。参数含检查的 UB 地址范围和读写模式。仅 a2/a3 支持。

<!-- cannbot:related:start -->
## 相关

- [AscendcAssert](ascendc_assert.md)（`related`）：《AscendcAssert》说明CPU/NPU域断言接口，当断言条件不满足时输出断言信息并格式化打印，主要用于调试阶段。；《CheckLocalMemoryIA》说明检查设定范围内UB读写行为的调试接口，有设定范围的读写行为会触发EXCEPTION报错。。二者在AscendcAssert属于异常检测工具链，与Assert、Trap和本地内存检查共同完成设备侧失败定位上存在可执行的直接衔接。
- [LocalMemAllocator](../../resource_management/local_mem_allocator/local_mem_allocator.md)（`related`）：CheckLocalMemoryIA 与《LocalMemAllocator》的实质衔接是：CheckLocalMemoryIA 通过保留的 UB 地址范围触发异常，需结合 LocalMemAllocator、地址空间转换与 ASCENDC_DUMP 调试开关定位本地内存越界。
- [LocalMemAllocatorConstructor](../../resource_management/local_mem_allocator/local_mem_allocator_constructor.md)（`related`）：CheckLocalMemoryIA 与《LocalMemAllocatorConstructor》的实质衔接是：CheckLocalMemoryIA 通过保留的 UB 地址范围触发异常，需结合 LocalMemAllocator、地址空间转换与 ASCENDC_DUMP 调试开关定位本地内存越界。
- [LocalMemAllocator简介](../../resource_management/local_mem_allocator/local_mem_allocator_intro.md)（`related`）：CheckLocalMemoryIA 与《LocalMemAllocator简介》的实质衔接是：CheckLocalMemoryIA 通过保留的 UB 地址范围触发异常，需结合 LocalMemAllocator、地址空间转换与 ASCENDC_DUMP 调试开关定位本地内存越界。
- [LocalMemBar](../../reg_vector_compute/sync_control/local_mem_bar.md)（`related`）：LocalMemBar 与《CheckLocalMemoryIA》的实质衔接是：LocalMemBar 只解决本地内存可见性，AscMemBar/核内同步材料给出作用域；RAW 故障与 arch35 编译卡分别验证缺 barrier 和错误执行域的后果。
- [ReserveLocalMemory](../../../../utils_api/platform_info/platform_ascend_c/reserve_local_memory.md)（`related`）：CheckLocalMemoryIA 与《ReserveLocalMemory》的实质衔接是：CheckLocalMemoryIA 通过保留的 UB 地址范围触发异常，需结合 LocalMemAllocator、地址空间转换与 ASCENDC_DUMP 调试开关定位本地内存越界。
- [__cvta_generic_to_local](../../../../simt_api/address_space_conversion_functions/_cvta_generic_to_local.md)（`related`）：CheckLocalMemoryIA 与《__cvta_generic_to_local》的实质衔接是：CheckLocalMemoryIA 通过保留的 UB 地址范围触发异常，需结合 LocalMemAllocator、地址空间转换与 ASCENDC_DUMP 调试开关定位本地内存越界。
- [__isLocal](../../../../simt_api/address_space_predicate_functions/_is_local.md)（`related`）：CheckLocalMemoryIA 与《__isLocal》的实质衔接是：CheckLocalMemoryIA 通过保留的 UB 地址范围触发异常，需结合 LocalMemAllocator、地址空间转换与 ASCENDC_DUMP 调试开关定位本地内存越界。
- [关闭ASCENDC_DUMP说明](../disable_ascendc_dump.md)（`related`）：CheckLocalMemoryIA 与《关闭ASCENDC_DUMP说明》的实质衔接是：CheckLocalMemoryIA 通过保留的 UB 地址范围触发异常，需结合 LocalMemAllocator、地址空间转换与 ASCENDC_DUMP 调试开关定位本地内存越界。
- [异常检测](exception_detection.md)（`related`）：《异常检测》说明异常检测接口集，包含 ascendc_assert、assert、Trap、CheckLocalMemoryIA(ISASI) 等接口。；《CheckLocalMemoryIA》说明检查设定范围内UB读写行为的调试接口，有设定范围的读写行为会触发EXCEPTION报错。。二者在异常检测索引把AscendcAssert、Assert、Trap和CheckLocalMemoryIA组成设备侧诊断入口上存在可执行的直接衔接。
- [Assert](assert.md)（`same_topic`）：CheckLocalMemoryIA 与《Assert》的实质衔接是：CheckLocalMemoryIA 通过保留的 UB 地址范围触发异常，需结合 LocalMemAllocator、地址空间转换与 ASCENDC_DUMP 调试开关定位本地内存越界。
- [Trap](trap.md)（`same_topic`）：CheckLocalMemoryIA 与《Trap》的实质衔接是：CheckLocalMemoryIA 通过保留的 UB 地址范围触发异常，需结合 LocalMemAllocator、地址空间转换与 ASCENDC_DUMP 调试开关定位本地内存越界。
<!-- cannbot:related:end -->
