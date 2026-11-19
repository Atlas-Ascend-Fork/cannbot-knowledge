---
type: Guide
title: TorchNPU 通信内存：P2P 缓冲、零拷贝与对称堆
description: 区分每通信域独占的 P2P 缓冲、实验零拷贝和 NPUSHMEM 对称堆，不与计算缓存分配器混算。
tags:
- task.optimization
- topic.parallelism
- topic.memory
status: stable
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/collective_communication/P2P_HCCL_BUFFSIZE.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/collective_communication/（beta）TORCH_HCCL_ZERO_COPY.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/memory_management/NPU_SHMEM_SYMMETRIC_SIZE.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/collective_communication/P2P_HCCL_BUFFSIZE.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/collective_communication/（beta）TORCH_HCCL_ZERO_COPY.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/memory_management/NPU_SHMEM_SYMMETRIC_SIZE.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/distributed/ProcessGroupHCCL.cpp
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/distributed/ProcessGroupHCCL.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/NPUCachingAllocator.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/distributed/symm_mem/NPUSHMEMExtension.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/register/OptionsManager.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/core/npu/register/OptionsManager.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/distributed/Init.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/distributed/symm_mem/NPUSHMEMInterface.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/distributed/symm_mem/NPUSHMEMSymmetricMemory.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/distributed/symm_mem/NPUSymmetricMemoryUtils.hpp
  role: implementation
created_at: '2026-11-09T06:08:21Z'
updated_at: '2026-11-14T01:56:26Z'
platforms:
- a2
- a3
---

# TorchNPU 通信内存：P2P 缓冲、零拷贝与对称堆

## 固定版本与范围

依据 TorchNPU 固定主线 `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf`，限定来源声明支持的 A2/A3；逐项版本门槛独立核对，不回推至 26.0/PyTorch2.8 发布基线。本文仅静态审阅，没有 NPU 实验。

## P2P 独立通信域的容量代价

P2P_HCCL_BUFFSIZE默认20MB（来源说明TorchNPU7.1起默认如此）；0复用默认域，≥1建立独立P2P域并配置缓冲大小。每个独立域独占发送、接收各一份，总量为2倍配置值，不能与其他业务内存复用；域多时累积占用可能导致OOM。

增大缓冲可能有利于大P2P数据，减小可节省常驻量；0还改变域选择，不能只当减少20MB。新建独立域时send/recv下发间隔长可能建链超时，先核对通信顺序和HCCL_CONNECT_TIMEOUT，不把文档600秒示例当统一最佳值。

## 零拷贝与对称堆是不同功能

TORCH_HCCL_ZERO_COPY为仅列A3的实验功能，默认0，1减少片内拷贝及计算通信争抢带宽；依赖expandable_segments=True，文档明确不支持TorchAir场景。它不取消业务数据依赖，也不能与所有图后端直接组合。

NPU_SHMEM_SYMMETRIC_SIZE为NPUSHMEM设备间直接访问设置对称堆，默认1GiB；可用正数字节数或K/M/G/T后缀，非法格式报错。首次读取缓存，用于初始化对称内存区域，运行中更改不重设现有堆。它不是P2P_HCCL_BUFFSIZE或HCCL通信域缓冲的统一别名。

分别记录域数量、业务数据、对称堆和计算池占用，再比较通信耗时及峰值，不能用empty_cache预期归还所有通信内存。本文未初始化通信域、对称堆或测量收益。

## 对称堆的首次读取与产品范围

中英文NPU_SHMEM_SYMMETRIC_SIZE页均列A2/A3及950DT，数字字节数或k/K、m/M、g/G、t/T后缀必须为正数，非法格式报`NPU_SHMEM_SYMMETRIC_SIZE is invalid`。首次OptionsManager::GetShmemSymmetricSize读取后缓存，传给aclshmemx_init_attr或shmem_set_attr初始化；堆太小可导致对称内存分配失败，运行中改环境不能重设现有堆。

上述对称堆及P2P产品表不能扩大零拷贝范围：同提交两语言的TORCH_HCCL_ZERO_COPY实验页**只列A3**。本卡按段落使用产品范围，A2支持其他通信内存配置不代表支持该零拷贝开关，950DT也不在其产品表中。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/collective_communication/P2P_HCCL_BUFFSIZE.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/collective_communication/（beta）TORCH_HCCL_ZERO_COPY.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/memory_management/NPU_SHMEM_SYMMETRIC_SIZE.md)（constraint）

- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/collective_communication/P2P_HCCL_BUFFSIZE.md)（constraint）

- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/collective_communication/（beta）TORCH_HCCL_ZERO_COPY.md)（constraint）

- [固定来源 6](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/memory_management/NPU_SHMEM_SYMMETRIC_SIZE.md)（constraint）


## 零拷贝启用链

文档页只给开关与前提；实现上该功能在**首个全局 ProcessGroupHCCL 构造**时一次性启用（主线 :1347-1381，发布版 :1170-1200 同构，仅行号差）：仅当 `options_->global_ranks_in_group` 为空（该实例即 `global_`）才尝试。门槛依次为 `OptionsManager::IsHcclZeroCopyEnable()`（解析 TORCH_HCCL_ZERO_COPY，0/1 之外抛 VALUE，两版同）与 `NPUCachingAllocator::checkConfigExpandableSegments()`；随后 `checkEnvVarOrLogWarning`（主线 :385-432）要求启动器注入的 LOCAL_RANK、RANK、GROUP_RANK、LOCAL_WORLD_SIZE 四个环境变量齐全，缺任一则 WARN_ONCE 提示用 torchrun 并整体禁用。齐全时按 LOCAL_RANK 惰性初始化设备（NpuSysCtrl 未初始化则 Initialize，当前设备号不同则直接 SetDevice 覆盖），再用 store 协商一个专用 HCCL 域：key 为 `hccl_zero_copy_{GROUP_RANK}_{hcclCommCounter_}`，本地 LOCAL_RANK==0 的一端 hcclGetRootInfo 写 store，其余读 store；该域以 LOCAL_WORLD_SIZE/LOCAL_RANK 创建，源码注释明确**仅供零拷贝、不承载通信算子、不设 commName**（:3215-3270）。最后 `buildServerMemMapForHccl(device_id, comm)`（NPUCachingAllocator.cpp :1789-1796）把 comm 存进该设备分配器并 setHcclComm 到全部既有 expandable_segments——本设备只允许建一次，重复建触发 INTERNAL 断言「Build HCCL server group redundancy」。因此该功能的失败模式是：设备未用 torchrun 拉起、expandable_segments 未开或环境不全时只在 HCCL 日志留一条 INFO/WARN，不报错。

## 窗口注册与零拷贝互斥

`windowRegisterAndExchange`（主线 :3511-3526，发布版 :2944-2960）经 `_window_register_and_exchange` / `_get_window_mem` 暴露（Init.cpp :404-409）：windowSize 必须 >0，`windowMem_` 只允许注册一次（UNAVAIL），且**设置了 TORCH_HCCL_ZERO_COPY 时被直接拒绝**（UNAVAIL）——零拷贝模式与显式窗口注册互斥。注册即 `at::empty` kChar 张量 + `hcclCommRegister` + `hcclCommExchangeMem(peerRanks)`。该项两版均有。

## 通信域内存池注册层

主线新增三件，发布版全无（负向证据：发布文件无 getMemAllocator/registerMemPool/deregisterMemPool）：`getMemAllocator`（:3445-3455）给 c10d Backend 的 `mem_allocator` 属性提供 HCCL 专用分配器，门槛 CANN >= 9.2.0-beta，否则 TORCH_CHECK NOT_SUPPORT——注意版本门槛挂在分配器本身而非 `supportsTensorAlloc()`，后者基类仍答 false；分配器由 `NPUPluggableAllocator::createCustomAllocator(_hcclMemAlloc, _hcclMemFree)` 构造（:3433-3443），底层是 hcclMemAlloc/hcclMemFree。`registerMemPool`（:3457-3480）要求通信域已存在（UNAVAIL，错误文案提示 init_process_group 传 device_id 提前初始化），把 pool 记进 `hcclCommMemPoolMap` 并对快照中该 pool 已拥有的全部 segment 立即 registerSegment（errorOnRereg=false，symmetric 透传）；随后 `attachAllocatorHooks`（:3390-3431）把分配器的 SEGMENT_ALLOC/SEGMENT_FREE 轨迹钩子接到同一 map：之后该池新 segment 分配/释放即自动向已登记 comm registerSegment/deregisterSegment。`deregisterMemPool`（:3482-3509）要求先注册过（UNAVAIL）。该层是与 expandable_segments/私有池协作的零拷贝注册面，发布快照无此能力。

## NPU_SHMEM_SYMMETRIC_SIZE 的解析面与文档差异

文档页写「配置值必须为正数」；实现（OptionsManager::GetShmemSymmetricSize，主线 :771-811，发布版 :684-722 同构）**没有正数校验**：`sscanf(env_val, "%lf%c%c", &p, &f, &rest)`，纯数字（返回 1）与「数字+单字符后缀」（返回 2）都通过，0、负数、小数乃至科学计数都会被解析并按 `ceil(p * 2^scale)` 向上取整——取整规则文档未记；多写一个尾字符（返回 3）或未知后缀才抛 `NPU_SHMEM_SYMMETRIC_SIZE is invalid`。因此「必须为正数」只是使用约定，非法的是格式不是符号。消费链核实：`initialize_npushmem_with_store`（NPUSHMEMExtension.cpp :21-105）首次调用时读取并缓存（static），按 HCCL 运行时符号存在性二选一——`Aclshmemx_get_uniqueid_exist()` 为真走 `aclshmemx_init_attr(ACLSHMEMX_INIT_WITH_UNIQUEID)`，否则走 `Shmem_set_attr`+`Shmem_set_attr_uniqueid_args`——与文档「传给 aclshmemx_init_attr 或 shmem_set_attr」的描述一致，但文档未说明这是按 HCCL 库能力自动二选一，且只在 NPUSHMEM 初始化路径首次查询时读一次。

## 补充来源

- [固定来源 7](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/distributed/ProcessGroupHCCL.cpp)（primary）：:1347-1381、:385-432、:3215-3270、:3390-3455、:3457-3509、:3511-3526。

- [固定来源 8](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/distributed/ProcessGroupHCCL.cpp)（implementation）：:1170-1200、:2944-2960；负向证据：无 mempool/allocator 层。

- [固定来源 9](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/NPUCachingAllocator.cpp)（implementation）：:1789-1796。

- [固定来源 10](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/distributed/symm_mem/NPUSHMEMExtension.cpp)（implementation）：:21-105。

- [固定来源 11](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/register/OptionsManager.cpp)（implementation）：:771-811、:79-86。

- [固定来源 12](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/core/npu/register/OptionsManager.cpp)（implementation）：:37-47、:684-722。

- [固定来源 13](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/distributed/Init.cpp)（implementation）：:404-409。

## 对称内存分配器与 SymmetricMemory 源级边界

`NPUSHMEMSymmetricMemoryAllocator`（NPUSHMEMSymmetricMemory.cpp:176-291）以名字 `"NPUSHMEM"` 注册为 PrivateUse1 的对称内存分配器（静态注册器 :279-286）：`alloc` 直接 `Aclshmem_malloc(size)` 并把指针记入 `allocations_`（:176-211，未定义 `has_multicast_support` 的设备侧查询——该方法直接抛 NOT_SUPPORT）；`rendezvous(ptr, group_name)` 要求 group_name 存在且 ptr 必须由本分配器分配（否则 TORCH_CHECK），按 `(ptr, group)` 缓存返回（:235-260）。`NPUSHMEMSymmetricMemory` 构造（:40-108）经 group store 一次性 all_gather 交换 rank→global_rank 映射（每组缓存一次），再用 `Aclshmem_ptr(ptr, global_rank)` 取各 rank 对应远端地址构成 `buffers_`；`signal_pads_/buffers_dev_/rank_to_global_rank_dev_` 标注 "to be done" 未实现，`has_multicast_support()` 固定 false，`barrier/put_signal/wait_signal` 三个信号原语全部抛 NOT_SUPPORT（:116-148），`get_offset()` 恒 0（:272-275）。因此当前 NPUSHMEM 对称内存只提供"分配 + 各 rank 地址表 + put/get on stream"（NPUSHMEMInterface.cpp:176-200 经 `aclshmemx_putmem_on_stream/aclshmemx_getmem_on_stream` 动态解析，`Aclshmem_ptr` 按 `aclshmem_ptr`→`shmem_ptr` 双符号回退，:196-210），不做设备侧信号同步与多播；把 torch symmetric memory 的 barrier/信号语义套到 NPUSHMEM 上会得到显式 NOT_SUPPORT 而非静默错误。`Aclshmem_finalize` 的存在性探测吞掉 libshmem.so 缺失常量并返回 false（:212-229）。本节未审阅 NPUSymmetricMemoryUtils.hpp 的模板工具与 npu 对称内存 Python 绑定面。

## 补充来源

- [固定来源 14](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/distributed/symm_mem/NPUSHMEMInterface.cpp)（implementation）：:176-229（put/get on stream、Aclshmem_ptr 双符号回退、finalize 存在性探测）。

- [固定来源 15](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/distributed/symm_mem/NPUSHMEMSymmetricMemory.cpp)（implementation）：:33-148（构造/rank 映射交换/未实现原语清单）、:176-291（alloc/rendezvous/注册器）。

## 发布版本 对照（f3ecfe4a）

卡内涉及的 5 个发布孪生文件已做真实机械比对（sha256 → 去空白 → token → 注释剥离 token → 语义 diff 五级），结论分述如下。

### 已绑定（等价/无行为差异）

- `torch_npu/csrc/distributed/symm_mem/NPUSymmetricMemoryUtils.hpp`：全空白折叠后逐字节等价（重排版）。发布来源条目已入 frontmatter（release pin f3ecfe4a）。

### 版本边界（发布版本 行为不同，按 pin 分述）

- **`torch_npu/csrc/distributed/symm_mem/NPUSHMEMInterface.cpp`**：发布版删除 Shmem_（非 x 符号）助手，宏重命名。
  - 发布版删除 `Shmem_putmem_on_stream`/`Shmem_getmem_on_stream` 定义（libshmem 非 x 符号路径）；卡内所述 `aclshmemx_putmem_on_stream`/`aclshmemx_getmem_on_stream` 动态解析路径两版均保留。
  - 其余差异为宏重命名（TORCH_NPU_LOAD_FUNC→LOAD_FUNCTION 等），加载逻辑一致。
  - 对本卡结论的影响：本卡 put/get on stream 结论两版成立；主线额外的 Shmem_* 助手在发布版本 不存在，不能在发布版引用该路径。
- **`torch_npu/csrc/distributed/symm_mem/NPUSHMEMInterface.h`**：发布版接口面删除两条声明。
  - 发布版删除 `void Shmem_putmem_on_stream(...)`/`void Shmem_getmem_on_stream(...)` 声明与 `#include <acl/acl_base.h>`；`Aclshmem_ptr`/`Aclshmem_finalize*` 声明两版一致。
  - 对本卡结论的影响：本卡「Aclshmem_ptr 双符号回退」结论不受影响（Aclshmem_ptr 在两版 .h 均有）；Shmem_* 声明仅主线存在。
- **`torch_npu/csrc/distributed/symm_mem/NPUSHMEMSymmetricMemory.cpp`**：对称内存原语与缓存结构为两版主要差异。
  - 主线 barrier/put_signal/wait_signal 三个信号原语抛 "does not support"（:128-149）；发布版三者为空实现 no-op（仅 `// to be done` 注释，:148-167），不报错也不做事。
  - 主线 rank→global_rank 映射用进程级 static map（`rank_to_global_rank_map`+`std::mutex`，:17、:53-72）；发布版改为每实例成员 `rank_to_global_rank_`（来自 group_info，:50-67）。
  - 发布版新增 `get_buffer`/`get_signal_pad`（均抛 NOT_SUPPORT，:128-145）与 `get_signal_pad_size()`=2048（:113）、`get_rank_to_global_rank_dev()`（:184-186）；主线 `get_offset()`（恒 0，:274）在发布版删除。
  - 分配器：主线 alloc/rendezvous 以 `std::lock_guard<std::mutex>` 串行化且静态注册器带 `name()`="NPUSHMEM"；发布版无锁（源码注释 `to be done: thread safety`，:212）且注册不带 name/supported_device_type 覆盖（:263-272），alloc 时经 `get_group_info("0")` 初始化 npushmem（:201-206）。
  - 日志宏 TORCH_NPU_SYMMEM_LOGD 全部改为 logger->debug。
  - 对本卡结论的影响：本卡「信号原语全部抛 NOT_SUPPORT」「get_offset() 恒 0」「以名字 NPUSHMEM 注册」均只描述主线；发布版本 的 barrier/put_signal/wait_signal 是静默 no-op、无 name() 注册、无锁保护，结论需按 pin 分述。
- **`torch_npu/csrc/distributed/symm_mem/NPUSHMEMSymmetricMemory.hpp`**：头文件接口面随实现差异同步变化。
  - 主线 `size_t get_offset() override` 与 `c10::Device get_device() override` 在发布版分别改为 `get_signal_pad_size()` 与 `get_rank_to_global_rank_dev()` 等。
  - 发布版新增 `get_buffer`/`get_signal_pad` 声明与成员 `std::vector<int> rank_to_global_rank_`、`int* rank_to_global_rank_dev_`；删除 `std::mutex mutex_`、GetSymmMemLogger/LOGD 宏与 `#include <mutex>`/LogContext.h。
  - 发布版另删除分配器 `supported_device_type()`/`name()` override 声明。
  - 对本卡结论的影响：本卡对该类的原语清单与注册描述需以主线版本 为准；发布版本 接口面是另一形态。

（本节静态比对，未运行/未编译；结论按文件分列，未列出的文件未比对。）
