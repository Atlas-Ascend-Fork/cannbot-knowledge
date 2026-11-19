---
type: Guide
title: Host锁页分配与注册：首次选路、能力回退和注销
description: 追踪Host allocator注册及pin入口，说明pinned_mem_register的实际能力门控、按块注销、脚本侧npurt锁页链与裸运行时绑定边界。
tags:
- task.optimization
- topic.memory
- topic.performance.analysis
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/CachingHostAllocator.cpp
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/core/npu/CachingHostAllocator.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/aten/common/PinnedMemoryAllocator.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/NPUHooksInterface.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/CachingHostAllocator.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/NPUAllocatorConfig.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/npu/npurt.cpp
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/_pin_memory_utils.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_init/core/module_loader.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/contrib/transfer_to_npu.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/contrib/transfer_to_npu.py
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/InitNpuBindings.cpp
  role: implementation
created_at: '2026-11-10T14:30:17Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# Host锁页分配与注册：首次选路、能力回退和注销

本卡定向审阅TorchNPU主线`ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf`的普通Host pinned allocator覆盖函数和实际入口，并对照发布`f3ecfe4a7ef7395754da7ca2e35661a7132b519b`的注册/分配释放段。两版有设备guard、reserve及接口差异，不声明全部Host缓存实现相同。平台未知，保持draft、空平台；未执行上游、Host申请、设备传输或性能实验。

## 实际接线和pin入口做的工作

REGISTER_HOST_ALLOCATOR将hostAllocator注册到PrivateUse1；NPUHooksInterface和getPinnedMemoryAllocator都返回该类Host allocator。NPUCachingHostAllocator的allocate返回CPU DataPtr，以ptr与ctx分开保存，并由raw_local_deleter转交free。外层allocate/free/record_event/empty_cache先经过setAllocator，call_once首次选择普通或expandable实现；之后改变环境不等于切换已选实例。

所读NPUNativeFunctions::_pin_memory以computeStorageNbytes(sizes,strides,itemsize)申请Host Storage，再用原sizes/strides构造CPU Tensor并copy_(self)。这是进入这一准确本地入口之后的新存储/复制行为，不是仅设置一个pinned布尔位，也不证明更上层已pinned对象一定重复分配。stride存储跨度与numel字节数应分开核对。

普通实现继承上游ATen CachingHostAllocatorImpl。主线把background thread、最大舍入/缓存阈值等配置作为override getter传给基类；本卡未固定并审完上游基类的完整缓存和舍入消费者，不能据getter存在认证每次申请/释放策略。配置合同复用[pinned选项](torch_npu_pinned_memory_options.md)，与[copy_的Host指针后处理](torch_npu_host_device_copy_execution.md)分开。

## 实际Host注册需要多个条件

普通slowpath先设host_registered=False。只有AclrtMallocHostWithCfg符号存在且函数内静态va_feature_support仍为True时，才用VA_FLAG=1申请；成功后且有效pinned_mem_register为True，才调用AclrtHostRegisterV2(...,ACL_HOST_REG_MAPPED)，再将该块记录为已注册。

| 所选分支 | 后续行为 |
| --- | --- |
| WithCfg返回FEATURE_NOT_SUPPORT | 将va_feature_support置False，必要时告警，并退回aclrtMallocHost；这次不调用HostRegisterV2。 |
| WithCfg其他错误 | NPU_CHECK_ERROR处理，不描述为任意错误都自动回退。 |
| WithCfg不存在或该进程已禁用VA路线 | 直接aclrtMallocHost；slowpath本分支不再执行HostRegisterV2。 |

主线配置解析还会因WithCfg接口不可用，或与Host expandable同配，把pinned_mem_register改为False并告警。环境文字为True、符号存在、pinned内存可申请与实际HostRegisterV2已发生是不同证据。slowpath告警的驱动版本文字不是本卡重新核实的完整支持下限，配套门槛仍按配置文档。

成功指针进入npu_ptrs集合，并以use_host_register[ptr]保存本次是否实际注册。因此copy侧ptr_exist只证明选定allocator识别该地址，不等同“此块一定走过HostRegisterV2”。已有Pinned/Host属性判断也不独立证明跨流生命周期或零拷贝收益。

## 释放按每块记录注销，缓存归还另有时机

普通free_block_slowpath读取该指针的注册记录：True时先AclrtHostUnregister，再aclrtFreeHost，成功后移除记录；未注册块直接FreeHost。这个override处理真正退还Host内存，不表示Tensor析构会立即触发它；普通块何时离开上游缓存池仍需对应基类消费者。

主线在正常slowpath之前还可先尝试reserve segment；该segment从同一slowpath获取大块，再委托上游PinnedReserveSegment分配。其拥有的子块在本地free_block中只移出识别集合并返回，不按每个子块调用FreeHost/Unregister。完整reserve子分配/回收算法未在本卡闭合，不能把普通slowpath按块规则机械套到此路线。发布所读普通实现没有这一段相同reserve入口。

主线Host慢申请/慢释放耗时写入微秒Duration统计，但该计时只包围所选函数，不是整个pin_memory、缓存命中或H2D端到端耗时；未读取运行计时。普通record_stream会在HostFinalize时直接返回；query_event遇异常记录后返回True，属于错误清理分支，不能当成设备计算成功或正确性保证。

## 类型判断和组合边界

is_pinned本地入口仅对CPU Tensor继续，检查storage基地址；当ACL属性接口存在但NPU尚未初始化时，所读helper返回False，存在属性时比较HOST，否则退回本allocator地址集合。它与每块注册记录、实际传输和所有权协议分别判断，不能从一次is_pinned结果恢复完整申请历史。

优化评估应固定实际Host实现、首次配置、注册能力、Tensor stride及存储跨度、缓存命中与数据转移；再分别比较申请、注销和H2D/CPU时间。主线与发布局部覆盖函数不能认证同一上游ATen版本、外部Host注册对象或任意设备组合。

本卡不重写所有配置选项，未审完普通ATen缓存、reserve pool与所有异常回滚；没有新增运行verified、产品支持或吞吐结论。

## Evidence

- [固定实现来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/CachingHostAllocator.cpp)（primary）：定向范围 144–371, 1190–1217, 1246–1274, 1332–1335。
- [固定实现来源 2](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/core/npu/CachingHostAllocator.cpp)（implementation）：定向范围 168–314, 1153–1184, 1201–1242。
- [固定实现来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/aten/common/PinnedMemoryAllocator.cpp)（implementation）：定向范围 16–34。
- [固定实现来源 4](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/NPUHooksInterface.cpp)（implementation）：定向范围 60–65。
- [固定实现来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/CachingHostAllocator.h)（implementation）：定向范围 40–76。
- [固定实现来源 6](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/NPUAllocatorConfig.cpp)（implementation）：定向范围 325–339。

## 脚本侧已有内存锁页链与 npurt 裸运行时绑定

本卡前文覆盖 Host pinned 池的分配与 `pinned_mem_register` 注册。本节记录另一条链：把**已存在的 Host 内存**注册为页锁定，以及暴露给脚本的裸运行时绑定，两者都在主线 pin 内。

### npurt 绑定模块的创建与访问

| 实际门槛 | 动作 | 失败/版本边界 |
| --- | --- | --- |
| import torch_npu 时 `_initialize_c_extension_children`（module_loader.py:52-73） | 依固定顺序 `_create_child_once` 创建 `_C._npurt`（:64，`_npurt_init` 方法注册于 InitNpuBindings.cpp:244）；已存在则跳过 | `_npurt` 在 `_REQUIRED_C_EXTENSION_CHILDREN`（:10-17），缺失时 import 期 RuntimeError"Required torch_npu._C child submodules are missing" |
| 脚本调用 `torch_npu.npu.npurt()`（npu/__init__.py:264-292） | 先 `npu._lazy_init()`，再返回 `torch_npu._C._npurt` | 构建中无该子模块时 RuntimeError"unavailable in this build"；docstring 声明 flags 须遵循 CANN ACL Host Register 定义 |

四个绑定（npurt.cpp:21-51）：`npuHostRegister(ptr, size, flags)`、`npuHostUnregister(ptr)`、`npuStreamCreate(ptr)`、`npuStreamDestroy(ptr)`。每者的 `ptr==0` 直接返回整数 `ACL_ERROR_INVALID_PARAM`（不抛异常）；每次 ACL 调用都包 `py::gil_scoped_release`（:25/:33/:41/:49）——注册/注销/建流等阻塞调用期间不占 GIL；返回原始 aclError 整数，错误语义由 Python 调用方决定。`npuStreamCreate/Destroy` 在 torch_npu 树内没有 Python 消费点（全树 rg），是面向外部脚本的裸流入口，与[流池卡](torch_npu_native_stream_pools_and_external_identity.md)管理的 NPUStream 对象是不同层。

### _pin_memory_utils：页锁定注册与错误语义

`torch_npu/npu/_pin_memory_utils.py`（主线独有）提供 `pin_memory(data_ptr, size)`/`unpin_memory(data_ptr)`：以 `_ACL_HOST_REG_PINNED = 0x10000000` 调 `npurt().npuHostRegister`（:8-22）/`npuHostUnregister`（:25-31），返回非零即 RuntimeError，附错误码与 `pta_error(ErrCode.ACL)`。该模块经 `transfer_to_npu._patch_cuda` 把 `cuda._pin_memory_utils` 整体替换（transfer_to_npu.py:402-411）——经 shim 迁移的 CUDA 代码调用 `torch.cuda._pin_memory_utils.pin_memory` 时实际走 npurt 链；[transfer shim 卡](torch_npu_transfer_to_npu_shim_mechanism.md)记录了这一模块级替换，本节补其实现层。

与本卡前文的 ACL 注册区分：前文 `ACL_HOST_REG_MAPPED` 是 Host pinned 池按 `pinned_mem_register` 做 device-mapped 注册（CachingHostAllocator.cpp:253）；本节 `0x10000000`（PINNED）是对任意已有 Host 内存的页锁定——不同 flag、不同调用方，互不推导。页锁定只约束传输路径可行性，不是零拷贝或带宽收益的证明；未执行任何注册或传输。

版本边界：发布 pin 无 `_pin_memory_utils.py`、`csrc/npu/npurt.cpp`，`npurt` 全树 rg 零命中，release 的 `_patch_cuda` 补丁清单不含 `_pin_memory_utils`（仅 :37 一处同名的 Tensor 方法名列表，另一对象）——整条脚本侧锁页链是主线独有。

## npurt 与脚本侧锁页来源

- [固定源码](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/npu/npurt.cpp)（primary）：全文 1–78。
- [固定源码](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/_pin_memory_utils.py)（primary）：全文 1–31。
- [固定源码](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_init/core/module_loader.py)（implementation）：行段 1–75（必需子模块清单与创建序列）。
- [固定源码](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/__init__.py)（implementation）：行段 260–295（npurt() 访问器）。
- [固定源码](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/contrib/transfer_to_npu.py)（implementation）：行段 400–415（cuda._pin_memory_utils 替换清单）。
- [固定源码](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/contrib/transfer_to_npu.py)（constraint）：行段 30–45（发布 _patch_cuda 无该替换；:37 为 Tensor 方法名列表）。
- [固定源码](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/InitNpuBindings.cpp)（implementation）：行段 226–246（npurt_functions 方法注册 :244）。
