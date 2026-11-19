---
type: Guide
title: TorchNPU原生Workspace：按流缓存、扩容同步与释放入口
description: 追踪两版工作区分配器与Storage入口，区分按流复用、2MiB扩容、逻辑释放、强制无缓存及清池边界。
tags:
- task.optimization
- topic.memory
- topic.performance.analysis
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/NPUWorkspaceAllocator.cpp
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/NPUWorkspaceAllocator.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/core/npu/NPUWorkspaceAllocator.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/core/npu/NPUWorkspaceAllocator.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/framework/utils/OpPreparation.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/framework/utils/OpPreparation.cpp
  role: implementation
created_at: '2026-11-11T05:18:01Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# TorchNPU原生Workspace：按流缓存、扩容同步与释放入口

固定PyTorch主线ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf与发布f3ecfe4a7ef7395754da7ca2e35661a7132b519b，完整读取两版NPUWorkspaceAllocator.cpp/h；产品和完整部署组合待核，保持draft、空平台。未导入、构建或运行上游，没有分配/设备同步/并发/性能实验。两版独立完整读取，不把格式相似当成运行行为等价。

## 带stream和不带stream是不同分配入口

allocate_workspace(workspace_size, stream)直接交OpPreparation::unsafe_empty_workspace带stream重载。两版该重载均使用NPUWorkspaceAllocator::get和malloc_with_stream构造NPUStorageImpl，再生成Byte类型、Contiguous restride的NPUTensorImpl；不带stream重载使用普通NPUCachingAllocator及make_npu_storage_impl。不能仅凭同名workspace就把普通显存缓存池、工作区池和任意生成代码的缓冲生命周期合并；编译器中的占位头也不是这里的完整运行实现。

Workspace头文件导出get/init/malloc_with_stream/emptyCache/recordHistory/snapshot/getDeviceStats以及allocate_workspace。get返回全局workspace_allocator，init查询设备数并只补建缺少的DeviceWorkspaceAllocator；getDeviceStats先验device范围，malloc_with_stream的本地入口没有同一assertValidDevice调用。c10::Allocator的allocate(size)本身只取得设备并返回空指针DataPtr，不申请size字节；需要流的实际分配通过allocate_with_stream，不能把基类allocate当成完整替代入口。

## 每设备每stream一个保留块

DeviceWorkspaceAllocator持递归mutex，以aclrtStream为key保存WorkspaceBlock。每次缓存申请先算size+32，缺流记录则创建初始空块；只有现有size不足时扩容。扩容先对旧指针执行设备同步WithTimeout和aclrtFree，再扣reserved、通知相关追踪、清指针；新尺寸为ceil((size+32)/2MiB)*2MiB，并检查结果不少于请求。2MiB是块容量舍入；实际申请使用AclrtMallocAlign32与HUGE_ONLY，不能据舍入常量独立证明指针具有2MiB基址对齐。

新申请返回非成功即nullptr，外层随后读取HBM可用/总量并抛OutOfMemoryError，错误文字建议尝试TASK_QUEUE_ENABLE=1。这个本地函数没有自己执行多轮OOM重试、自动更改开关或清空所有缓存；建议文字也不证明对每个负载有效。扩容前先写block->size，新申请失败只返回nullptr，本地没有回滚该size，也未刷新requested_size/context；因此失败后的尺寸记录本身不证明有效指针已存在。已有块足够时复用原指针，没有在此重新同步或分配，也没有把requested_size更新为本次较小请求。

缓存依赖调用方的流执行和临时工作区协议：同一stream后续申请可返回同一块，不为同时存活的每个Tensor另造独立存储。带stream参数本身不证明跨流/跨线程使用安全；这里只说明局部锁和索引规则，未做并发验证。

## DataPtr析构和真正归还的区别

缓存DataPtr用local_raw_delete，转全局free(ptr)，通过allocated_ptrs查所属设备，找到后调用该设备free()。后者只扣allocated统计并通知区域释放，没有aclrtFree；大块持续保留供后续同流复用。外层新旧指针不同时才移除旧映射并登记新映射；get_allocated_device找不到时free不继续。这个映射用于本地回调，不是逐存活Tensor的独立分配表。

free()没有ptr参数，它扣的是该设备最后记录的allocated_size，并使用last_block/last_stream上报；不能将其解释为按传入旧指针追溯精确原始请求大小。stats的allocated_bytes每次申请按整个block->size增加，不是只按size增加；同一缓冲多次申请时需结合逻辑释放顺序，不能直接把该计数当成每个活跃Tensor的去重物理总量。

empty_cache(device, check_error)逐块aclrtFree、扣reserved并delete块对象，清该设备blocks；在这个内部函数中check_error仅用于日志，实际Free仍用NPU_CHECK_ERROR，本地未见先执行设备同步。调用方需满足相关生命周期和同步协议，不能用参数名推定任意错误均忽略。外层在清一个设备后调用allocated_ptrs.clear，清的是全局映射，而非只删该设备项；不把这个行为写成各设备映射天然隔离的保证。

## 强制无缓存和复制

CheckForceUncached为真时，非零请求直接申请size+32字节，不做缓存分支的2MiB容量舍入；DataPtr选择uncached_delete，先NPU_CHECK_WARN设备同步WithTimeout，再checked aclrtFree。零大小路径不申请，返回空指针DataPtr。raw_deleter根据调用时同一开关选deleter，缓存/无缓存语义不能混用。

copy_data直接使用同步aclrtMemcpy的DEVICE_TO_DEVICE，文件明确注明尚不支持COW/lazy_clone。这个覆盖函数不为工作区提供新的复制共享协议。普通缓存OOM及多流Event回收属于[缓存分配器重试](torch_npu_allocator_retry_gc_and_oom.md)和[跨流回收](torch_npu_allocator_stream_reclaim_and_lazy_order.md)，不把其算法自动套到此独立池。

工作区统计、快照合成与时间轴边界见[Workspace快照](torch_npu_native_workspace_snapshot_accounting_and_timestamps.md)。评估时固定实际分配入口、stream、缓存开关、请求序列、2MiB舍入后的保留容量及扩容同步成本；没有以源码静态分支宣称峰值或吞吐提升。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/NPUWorkspaceAllocator.cpp)（primary），读取范围 1–635。
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/NPUWorkspaceAllocator.h)（implementation），读取范围 1–46。
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/core/npu/NPUWorkspaceAllocator.cpp)（implementation），读取范围 1–617。
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/core/npu/NPUWorkspaceAllocator.h)（implementation），读取范围 1–42。
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/framework/utils/OpPreparation.cpp)（implementation），读取范围 413–447。
- [固定来源 6](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/framework/utils/OpPreparation.cpp)（implementation），读取范围 410–447。
