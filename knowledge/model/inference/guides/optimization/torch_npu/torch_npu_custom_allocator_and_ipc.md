---
type: Guide
title: TorchNPU IPC 共享与自定义分配器组合边界
description: 区分 IPC 共享与替换分配器，记录 IPC 最低配套（spawn、HDK/CANN）与 950DT 边界，覆盖 _share_npu_/_new_shared_npu
  源级 C++ 链的同步事件、引用计数与 limbo 语义。
tags:
- task.design
- topic.memory
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/developer_notes/memory_management/virtual_memory.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/developer_notes/memory_management/custom_memory_allocator.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/developer_notes/memory_management/memory_sharing_ipc.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-npu/torch-npu-npu-NPUPluggableAllocator.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/npu/NPUPluggableAllocator.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/npu/Module.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/developer_notes/memory_management/custom_memory_allocator.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/developer_notes/memory_management/memory_sharing_ipc.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/multiprocessing/reductions.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_init/patches/api_patches.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/multiprocessing/reductions.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/ipc/StorageSharing.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/ipc/StorageSharing.h
  role: header
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/ipc/NPUIPCTypes.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/ipc/NPUIPCTypes.h
  role: header
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/ipc/StorageSharing.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/ipc/StorageSharing.h
  role: header
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/ipc/NPUIPCTypes.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/ipc/NPUIPCTypes.h
  role: header
created_at: '2026-11-09T02:11:09Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# TorchNPU IPC 共享与自定义分配器组合边界

## 证据与适用性

依据固定主线文档，平台支持仍有缺口，本卡为 draft、platforms 为空。IPC 文档页明确不支持 950DT；自定义分配器产品页对 950DT 的相互冲突见[生命周期指南](torch_npu_pluggable_allocator_lifecycle.md)。核对实际配套前不承诺该平台。

## 自定义分配器

NPUPluggableAllocator 的加载、切换时机、回调 ABI 与能力边界由[生命周期指南](torch_npu_pluggable_allocator_lifecycle.md)持有；本卡只记录其与 IPC 的组合边界，不重复基础说明。

## IPC 共享

共享通过 handle、storage_size、storage_offset 和重构函数恢复 Tensor/storage，减少跨进程拷贝。来源要求使用 spawn；可以通过 multiprocessing.Queue 发送 NPU Tensor，或先用 torch.multiprocessing.reductions.reduce_tensor，再重构。来源第二种方式允许接收方指定目标设备，但不能据此假定任意拓扑和设备映射都可跨卡访问，也不应把示例的 args[6] 索引固化为跨版本 ABI。

IPC 要求 HDK≥25.3.RC1 且 CANN≥8.3.RC1，明确不支持 950DT。虚拟内存扩展段、进程内自定义分配器和跨进程 IPC 是三个独立能力，分别核验，不推定组合支持。

## 验证

核对 .so 来源/导出函数、申请释放配对、发送与接收进程的设备映射、存储偏移和使用生命周期；比较同一共享存储的数值。未加载 .so、执行上游代码或设备共享实验。

- [缓存分配器选项与虚拟内存](../torch_npu_allocator_options.md)


## 已知范围与待确认范围

自定义分配器的独立 OpPlugin 产品页明确列出 A2/A3 训练支持；这不能提升为 IPC 的整卡平台矩阵。分别固定 TorchNPU、OpPlugin、HDK/CANN 及是否采用外部分配器后核验；本卡继续保留 draft，不用基础 API 的平台表替代组合支持。

## 单独分配器与 IPC 组合分开交付

A2/A3 的单独分配器接入见[初始化、回调 ABI 和能力边界指南](torch_npu_pluggable_allocator_lifecycle.md)。本卡保留 IPC 与组合证据缺口，不将单项 API 产品支持升级为 IPC 支持。

固定实现中 NPUPluggableAllocator 的 getIpcDevPtr/shareIpcHandle 直接提示未支持，普通 alloc/free 正常不能证明可沿用默认缓存分配器的 IPC 路径。

## 英文开发页的独立核对

同提交中英文开发页一致要求IPC使用spawn及HDK≥25.3.RC1/CANN≥8.3.RC1，并明确950DT暂不支持；自定义分配器页也明确排除950DT。它们没有消除OpPlugin接口页的产品冲突（见生命周期指南），本卡继续保留draft及空platforms。

IPC示例的1.0、3.14及同/跨卡输出只是历史样例值，不证明发送方退出、异步消费者、拓扑和外部分配器组合均正确。强化学习中训练/推理反复复制权重是该页给出的应用场景，实际仍按handle、storage大小/偏移、重构函数及双方设备/生命周期核对，不固定reduce_tensor返回的args[6]为通用ABI。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/developer_notes/memory_management/virtual_memory.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/developer_notes/memory_management/custom_memory_allocator.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/developer_notes/memory_management/memory_sharing_ipc.md)（constraint）
- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-npu/torch-npu-npu-NPUPluggableAllocator.md)（constraint）

- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/npu/NPUPluggableAllocator.cpp)（implementation）

- [固定来源 6](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/npu/Module.cpp)（implementation）

- [固定来源 7](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/developer_notes/memory_management/custom_memory_allocator.md)（constraint）

- [固定来源 8](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/developer_notes/memory_management/memory_sharing_ipc.md)（constraint）

- [固定来源 9](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/ipc/StorageSharing.cpp)（implementation），读取范围 1–287 全文

- [固定来源 10](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/ipc/StorageSharing.h)（header），读取范围 1–15 全文

- [固定来源 11](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/ipc/NPUIPCTypes.cpp)（implementation），读取范围 1–232 全文

- [固定来源 12](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/ipc/NPUIPCTypes.h)（header），读取范围 1–127 全文

## IPC 共享的源级 C++ 链

固定主线 ac0e1564 的 `torch_npu/csrc/ipc/` 四个文件闭合源级部分；平台/配套缺口维持不变。整个 StorageSharing.cpp 处于 `#ifndef BUILD_LIBTORCH` 守卫——**libtorch 构建不含 `_share_npu_`/`_new_shared_npu` 绑定面**。

`_share_npu_`（生产方）：先 TORCH_CHECK 设备为 PrivateUse1；存储描述必须是基础格式（`FormatHelper::IsBaseFormatType`），否则报「Try to share a storage without base format」——5 维格式 tensor 共享前需先转基础格式；`received_cuda()` 存储不可二次转发（须先 clone）。数据存在时经 `NPUCachingAllocator::shareIpcHandle` 取 handle+offset，`GetNewRefCountedSentData` 替换 storage 的 DataPtr（sent_data 持有原 DataPtr），IPC 事件句柄按需导出，返回 8 元组（device、handle、size_bytes、offset_bytes、ref_counter、ref_counter_offset、event_handle、event_sync_required）；offset 固定为字节单位（源注释：以 (handle, offset) 作共享缓存键，numel 不唯一）。零字节存储仍返回 8 元组，但 handle/ref_counter/event 为 None。

同步协议（NPUIPCTypes.cpp）：`IsSupportIpcEvent()` 且进程内计数 `sync_events_used_` 未达 `NPU_IPC_MAXIMUM_EVENTS_TO_USE=1000` 时，构造即 record 一个 `ACL_EVENT_IPC` 事件（`event_sync_required_` 为真）；否则对当前流做 `stream_synchronize` 全流同步（源注释：NPU 对可记录的阻塞型进程间事件数量有非官方上限，30000 个 record 即触发的场景为反例）。**当 `sync_events_used_` 达到 1000 后，该构造分支回退到当前流同步**；两固定实现中该计数在事件分支递增，未见递减。阈值对应此分支的计数，吞吐影响须按实际共享条件验证。引用计数：每个 shm 计数文件 10000 个 int64 槽（`NPU_IPC_REF_COUNTER_FILE_SIZE`），用 `at::RefcountedMapAllocator`（`NewProcessWideShmHandle`，SHAREDMEM|EXCLUSIVE）创建，初值 1，按槽位轮转。

`_new_shared_npu`（消费方）：event_sync_required 为真时把 IPC 事件 block 在当前流（等生产方就绪），否则无等待（生产方已做全流同步）；`getIpcDevPtr` 还原设备指针后按 offset 偏移，构造的 NPUStorageImpl 不可 resize 且 `set_received_cuda(true)`。DataPtr deleter 在释放时对当前流 `stream_synchronize`（best-effort，捕获异常）并把对应计数槽 `-1`（`ALLOCATOR_MAPPED_NOCREATE`，best-effort）。`NpuIPCCollect` 注册为缓存分配器的 `npu_ipc_collect` 空闲内存回调；计数>0 的已删块进 limbo（超过 1000 块告警一次），collect 只真正释放计数归零的块；生产方先于消费方退出时给一次性 WARNING（`~NpuIPCGlobalEntities` 检查 next_available_ref_counters_file_）。`_release_ipc_counter_npu` 单独递减计数；`_is_shared` 对 PrivateUse1 存储恒真。

## NPU Tensor/Event 的 reduce 注册链（主线，Python 面）

主线 `torch_npu/_init/patches/api_patches.py:21` 在 torch_npu 初始化的 api 补丁组调用 `_add_reductions_methods()`（`multiprocessing/reductions.py:172-183`）：先 `multiprocessing.reduction.register(torch.npu.Event, _npu_reduce_event)`，再把 `torch.multiprocessing.reductions` 的 `reduce_event/reduce_tensor/reduce_storage` 三个模块级名字替换为本仓版本，最后调用 `init_reductions()`。上文文档页允许的「Queue 发送 NPU Tensor」与「手动 reduce_tensor 再重构」两条路线，在主线都收敛到这组注册。

- Event（:22-28）：`event.ipc_handle()` 取 handle，重构走 `torch.npu.Event.from_ipc_handle(device, handle)`。
- Tensor（:31-96、:99-157）：主线版本包装上游 `reduce_tensor`——先取得上游 reduction，仅当其重构函数是 `rebuild_tensor` 且 storage 设备为 npu 时改走 NPU 分支：`storage._share_npu_()` 得到 (device, handle, storage_size_bytes, storage_offset_bytes, ref_counter_handle, ref_counter_offset, event_handle, event_sync_required) 并写入 shared_cache 弱引用；非 NPU storage 保持上游结果。重构函数 `rebuild_npu_tensor`：handle 为 None 或 0 字节 → 直接构造空 storage 不共享；缓存未命中 → `torch_npu.npu._lazy_init()` 后 `storage_cls._new_shared_npu(...)` 建共享 storage 并缓存弱引用；缓存命中（本进程已引用同一存储）→ `storage_cls._release_ipc_counter_npu(...)` 释放生产侧新计数器；随后按 offset/size/stride 重建 Tensor，Parameter 保持 requires_grad 参数语义。重构参数是位置元组，不承诺 `args[6]` 之类下标 ABI（与上文边界一致）。
- Storage（:160-169）：对 NPU storage 的直接 pickle 抛 `RuntimeError("Cannot pickle NPU storage; try pickling a NPU tensor instead")`；非 NPU storage 仍走上游 reduce。

消费边界：这条注册只覆盖 Python reduce/rebuild 面；`_share_npu_/_new_shared_npu/_release_ipc_counter_npu` 背后的 C++ 共享实现见上文「IPC 共享的源级 C++ 链」与「IPC C++ 链的发布孪生版本对照（pin f3ecfe4a）」；文档页的 HDK/CANN 门槛、spawn 要求与 950DT 边界不因注册存在而放宽。发布 pin f3ecfe4a 同名文件 diff 级全文对照：结构不同——发布版以完整实现替换 `reduce_tensor`（复制上游逻辑并插入 npu 分支，含非叶子 requires_grad 张量拒绝、named tensor 检查与 meta storage 分支），`reduce_storage` 同为含 file_system/fd 分支的完整替换；主线改为包装上游函数并新增 nested tensor 导入，CPU/非 NPU 语义随上游。两版共有 storage pickle 禁止与 `_new_shared_npu` 重构路径。本节为静态阅读，未跨进程传输 NPU Tensor，本卡维持 draft 与空 platforms。

## IPC C++ 链的发布孪生版本对照（pin f3ecfe4a）

上文源级 C++ 链的四个文件同时绑定发布 pin f3ecfe4a 同名来源，两 pin 全文对照结论如下；跨 pin 迁移结论时以各自固定提交为准，不据此放宽或收紧文档页的 HDK/CANN 门槛、spawn 要求与 950DT 边界。

- StorageSharing.h：两 pin 逐字节相同（sha256 一致），发布孪生无新增信息。
- NPUIPCTypes.h：仅重排版差异，空白折叠后词元等价（主线 127 行对发布版 151 行），声明与语义随主线。
- NPUIPCTypes.cpp：词元级仅 acl 头 include 由 `<acl/acl_base.h>`/`<acl/acl_rt.h>` 改为 `third_party/acl/inc/acl/...` 路径，其余完全等价；上文同步协议、事件用量上限与引用计数描述对两 pin 同样成立。
- StorageSharing.cpp：除 acl include 路径与整体重排版外有两处真实差异——`_new_shared_npu` 消费侧校验 handle 期望大小由主线常量 `c10_npu::kAclIpcHandleSize`（`NPUCachingAllocator.h` 内 `constexpr`，值 65）改为发布版 ACL 头宏 `ACL_IPC_HANDLE_SIZE`（`third_party/acl/inc/acl/acl_rt.h` 内定义，值同为 65，仅常量来源不同）；`THPStorage_NewWithStorage` 返回共享 storage 时发布版新增传递 `c10::impl::PyInterpreterStatus::TAGGED_BY_US` 解释器所有权标记，主线调用无此实参。`_share_npu_` 生产侧、8 元组与事件/计数语义词元级一致；解释器所有权标记相关行为不跨 pin 互推。
