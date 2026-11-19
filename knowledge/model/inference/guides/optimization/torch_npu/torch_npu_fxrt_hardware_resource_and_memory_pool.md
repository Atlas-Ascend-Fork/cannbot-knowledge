---
type: Guide
title: FXRT硬件资源层：设备上下文、流/事件与动态内存池
description: 记录FXRT自带硬件抽象层的实际行为：DeviceContext按设备名+id缓存、AscendResManager的外部分配器优先与内存池回退、VMM/dvpp多后端适配、动态内存池的512B对齐与1G扩展单元、多流控制器的事件池，以及ACL符号dlopen解耦。
tags:
- task.implementation
- topic.memory
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/hardware/device.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/hardware/hardware_abstract/device_context.h
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/hardware/hardware_abstract/device_context.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/hardware/hardware_abstract/device_context_manager.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/hardware/hardware_abstract/device_context_manager.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/hardware/hardware_abstract/device_event.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/hardware/hardware_abstract/dlopen_macro.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/hardware/hardware_abstract/capture_graph.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/hardware/hardware_abstract/stream_util.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/hardware/hardware_abstract/memory_manager.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/hardware/hardware_abstract/memory_manager.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/hardware/hardware_abstract/memory/abstract_dynamic_mem_pool.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/hardware/hardware_abstract/memory/abstract_dynamic_mem_pool.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/hardware/hardware_abstract/memory/dynamic_mem_pool.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/hardware/hardware_abstract/memory/dynamic_mem_pool.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/hardware/hardware_abstract/memory/mem_pool_util.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/hardware/hardware_abstract/memory/mem_pool_util.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/hardware/hardware_abstract/multi_stream_controller.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/hardware/hardware_abstract/multi_stream_controller.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/hardware/ascend/ascend_device_context.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/hardware/ascend/res_manager/ascend_res_manager.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/hardware/ascend/res_manager/ascend_res_manager.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/hardware/ascend/res_manager/ascend_stream_manager.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/hardware/ascend/res_manager/ascend_stream_manager.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/hardware/ascend/res_manager/ascend_event.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/hardware/ascend/res_manager/ascend_event.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/hardware/ascend/res_manager/ascend_hal_manager.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/hardware/ascend/res_manager/ascend_hal_manager.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/hardware/ascend/res_manager/capture_graph/ascend_capture_graph.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/hardware/ascend/res_manager/capture_graph/ascend_capture_graph.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/hardware/ascend/res_manager/mem_manager/abstract_ascend_memory_pool_support.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/hardware/ascend/res_manager/mem_manager/abstract_ascend_memory_pool_support.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/hardware/ascend/res_manager/mem_manager/ascend_dynamic_mem_adapter.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/hardware/ascend/res_manager/mem_manager/ascend_dynamic_mem_adapter.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/hardware/ascend/res_manager/mem_manager/ascend_gmem_adapter.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/hardware/ascend/res_manager/mem_manager/ascend_gmem_adapter.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/hardware/ascend/res_manager/mem_manager/ascend_memory_adapter.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/hardware/ascend/res_manager/mem_manager/ascend_memory_adapter.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/hardware/ascend/res_manager/mem_manager/ascend_memory_manager.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/hardware/ascend/res_manager/mem_manager/ascend_memory_manager.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/hardware/ascend/res_manager/mem_manager/ascend_memory_pool.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/hardware/ascend/res_manager/mem_manager/ascend_memory_pool.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/hardware/ascend/res_manager/mem_manager/ascend_vmm_adapter.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/hardware/ascend/res_manager/mem_manager/ascend_vmm_adapter.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/hardware/ascend/res_manager/symbol_interface/symbol_utils.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/hardware/ascend/res_manager/symbol_interface/symbol_utils.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/hardware/ascend/res_manager/symbol_interface/acl_symbol.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/hardware/ascend/res_manager/symbol_interface/acl_symbol.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/hardware/ascend/res_manager/symbol_interface/acl_base_symbol.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/hardware/ascend/res_manager/symbol_interface/acl_base_symbol.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/hardware/ascend/res_manager/symbol_interface/acl_compiler_symbol.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/hardware/ascend/res_manager/symbol_interface/acl_compiler_symbol.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/hardware/ascend/res_manager/symbol_interface/acl_mdl_symbol.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/hardware/ascend/res_manager/symbol_interface/acl_mdl_symbol.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/hardware/ascend/res_manager/symbol_interface/acl_op_symbol.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/hardware/ascend/res_manager/symbol_interface/acl_op_symbol.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/hardware/ascend/res_manager/symbol_interface/acl_rt_allocator_symbol.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/hardware/ascend/res_manager/symbol_interface/acl_rt_allocator_symbol.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/hardware/ascend/res_manager/symbol_interface/acl_rt_symbol.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/hardware/ascend/res_manager/symbol_interface/acl_rt_symbol.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/hardware/ascend/res_manager/symbol_interface/acl_tdt_symbol.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/hardware/ascend/res_manager/symbol_interface/acl_tdt_symbol.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/hardware/cpu/cpu_device_context.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/hardware/cpu/cpu_device_context.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/hardware/cpu/res_manager/cpu_res_manager.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/hardware/cpu/res_manager/cpu_res_manager.cpp
  role: implementation
created_at: '2026-11-13T04:14:49Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# FXRT硬件资源层：设备上下文、流/事件与动态内存池

## 固定来源与范围

固定TorchNPU主线ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf的FXRT自带硬件抽象层（src/hardware）。静态阅读，未初始化设备；整卡draft、platforms为空。FXRT执行模式选择、ACLGraph捕获窗口与NPUCachingAllocator的对接见[FXRT推理运行时](torch_npu_fxrt_runtime.md)，本卡只补硬件资源层的实际结构。

## 设备上下文按“设备名_id”缓存

`DeviceContextKey{deviceName, deviceId}`以字符串`<name>_<id>`为键；DeviceContextManager为每个键创建并缓存一个DeviceContext，各自持有DeviceResManager。Ascend侧ResManager聚合流管理、事件、HAL与内存管理；CPU侧是简化实现（无ACL依赖）。**“同名不同id是不同上下文”**——跨卡场景下每个deviceId独立初始化资源，上下文切换经HAL SetContext完成，不能假设一次Initialize覆盖所有卡。

## 分配内存：外部allocator优先，内存池回退

`AscendResManager::AllocateMemory`的行为分两支：**若上层注册了allocator（SetAllocator），先按CommonAlignSize对齐后完全交给该回调**——这正是运行时卡所述“捕获前后回调接TorchNPU NPUCachingAllocator”之外的通用外部分配入口；未注册时才走自带`memManager_->MallocMemFromMemPool`。FreeMemory同样deleter优先、否则FreeMemFromMemPool。`AllocateStaticMemory`（persistent路径）、FreePartMemorys（部分释放，保留地址列表外全放回）、DefragMemory、GetTotal*/Peak*统计都转发到内存池。**即FXRT显存归属由“是否注册外部allocator”决定**：注册后FXRT不拥有任何设备内存，未注册时全部走自有池。

## 动态内存池的实际参数与结构

抽象池（hardware_abstract/memory）定义buf/block两级结构与`DynamicMemBufStatus`（Idle/Used/EagerFree/UsedByEvent）：按tensor尺寸multimap找空闲buf、按设备地址map管理已用buf；512字节对齐（kDynamicMemAlignSize）、1GiB扩展单元（kDynamicMemAllocUnitSize）、**小于10MiB的请求按10MiB申请**（kMinimumAllocMem，注释说明是设备分配可能失败的经验值）；区分common与persistent两类池。Ascend落地有Default/DefaultEnhanced/BestFit三种池实现（BestFitAscendMemoryPool等）。多流安全依赖事件：释放带stream语义的buf须等待UsedByEvent状态解除。**这些常量是池行为边界**：大量小Tensor会被放大到10MiB粒度、相邻请求按512B对齐；把它们当成PyTorch caching allocator的参数是错的。

## 后端适配：VMM、GMEM、DVPP与符号解耦

Ascend侧内存有多个物理后端：`ascend_vmm_adapter`（VMM映射，按vmmAlignSize取整/裁剪、EagerFree、EmptyCache，统计已映射物理量）、`ascend_gmem_adapter`、`ascend_dynamic_mem_adapter`（DVPP类）与通用`ascend_memory_adapter`（HBM信息查询、按比例预留）。ACL全部接口经symbol_interface层dlopen解耦：acl_base/acl_rt/acl_mdl/acl_op/acl_tdt/acl_compiler/acl_rt_allocator各一个符号表文件，`CALL_ASCEND_API`/ORIGIN_METHOD宏统一转发，symbol_utils负责加载。**这使FXRT与ACL版本在符号层面解耦，但也意味着接口缺失在首次调用处才暴露**（如capture graph的aclmdlRI系列在AscendCaptureGraph析构/开始/结束处直接调用，缺符号即失败）。

## 流、事件、捕获图与多流控制器

`AscendStreamMng`是简单计数器式流id分配（ApplyNewStream/ApplyNewEvent递增），真实aclrtEvent经ApplyRtEvent创建并统一销毁；默认stream经GetStream暴露。`AscendEvent`按flag组合（TIME_LINE+SYNC、EXTERNAL、CAPTURE_STREAM_PROGRESS）创建。`AscendCaptureGraph`封装aclmdlRICaptureBegin/End与析构时的aclmdlRIDestroy（析构先SyncAllStreams，失败仅记日志）。`MultiStreamController`提供TaskIdOnStreamManager与EventPool：事件按creator懒创建、复用，配合任务id记录跨流依赖；这是FXRT自己图执行的多流原语，与TorchNPU的stream体系并存。

## 边界与验证方式

本卡未做任何设备初始化或分配：池参数（512B/1GiB/10MiB）、VMM开关、外部allocator接管行为都应按实际运行复核（用池统计接口对照GetTotal*/Peak*读数）。FXRT自有池与NPUCachingAllocator同时存在时，确认实际走了哪条路径（是否注册allocator）再谈显存峰值。dlopen符号缺失场景只验证了静态调用点，未实际触发。CPU路径仅静态存在性检查，未运行。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/hardware/hardware_abstract/device_context.h)（primary）：定向范围1–150。
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/hardware/ascend/res_manager/ascend_res_manager.cpp)（implementation）：定向范围110–190、405–440。
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/hardware/hardware_abstract/memory/dynamic_mem_pool.h)（implementation）：定向范围1–90。
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/hardware/ascend/res_manager/mem_manager/ascend_memory_pool.h)（implementation）：定向范围1–373。
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/hardware/ascend/res_manager/mem_manager/ascend_vmm_adapter.h)（implementation）：定向范围1–60。
- [固定来源 6](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/hardware/ascend/res_manager/mem_manager/ascend_memory_adapter.cpp)（implementation）：定向范围70–150。
- [固定来源 7](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/hardware/hardware_abstract/multi_stream_controller.cpp)（implementation）：定向范围28–210。
- [固定来源 8](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/hardware/ascend/res_manager/capture_graph/ascend_capture_graph.cpp)（implementation）：定向范围1–60。
- [固定来源 9](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/hardware/ascend/res_manager/ascend_stream_manager.h)（implementation）：定向范围1–60。
- [固定来源 10](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/hardware/cpu/res_manager/cpu_res_manager.cpp)（implementation）：全文件107行。
