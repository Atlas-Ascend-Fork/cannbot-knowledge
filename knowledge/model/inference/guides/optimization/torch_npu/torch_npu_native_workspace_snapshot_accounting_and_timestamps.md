---
type: Guide
title: TorchNPU Workspace快照：合成事件、统计口径与时间戳差异
description: 核对工作区history注册、快照合成、skip_actions与主线时钟转换，避免把保留块、逻辑使用和事件时间混为一谈。
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
created_at: '2026-11-11T05:18:01Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# TorchNPU Workspace快照：合成事件、统计口径与时间戳差异

固定PyTorch主线ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf与发布f3ecfe4a7ef7395754da7ca2e35661a7132b519b，完整读取两版NPUWorkspaceAllocator.cpp/h；产品和完整部署组合待核，保持draft、空平台。未导入、构建或运行上游，没有分配/设备同步/并发/性能实验。两版独立完整读取，不把格式相似当成运行行为等价。

## 统计与历史记录不是同一数据源

头文件DeviceStats仅含allocated_bytes和reserved_bytes，沿用Stat的current/peak/allocated/freed。update_stat按正负数更新累计，peak取current最大值。reserved在实际新分配/物理归还时增减；allocated在每次逻辑申请/释放按整块尺寸增减。每stream一个缓存块的实际路径见[Workspace缓存和deleter](torch_npu_native_workspace_stream_cache_and_deleters.md)，不能拿这两个字段互相替代，更不能直接替代设备总HBM占用。

非BUILD_LIBTORCH分支同时向Profiler上报WORKSPACE_ALLOCATOR、ALLOCATOR_INNER和相关分配/释放数据，按条件登记MsLeaks域/区域，并触发NPUTrace分配或释放回调。真实扩容与逻辑申请均有上报位置，逻辑释放与物理归还也分开；不能把每条MEMORY_MALLOC都计成一次底层aclrtMalloc。sum_mem随物理块增减，get_mem_size只是返回它，不是第三套已测量HBM总量。

## recordHistory设置与实际栈

两版record_history持锁，并要求when==NEVER或context_recorder非空；保存record_flag、条件context_recorder和record_context。maybeGatherContext无论level都直接返回nullptr，注释解释避免某些快照死锁，因此即使提供recorder，也不能据注册成功说此工作区实现保留了Python分配栈。context_when_allocated来自这个返回值。

主线额外接受skip_actions，先清集合并逐项用NPUCachingAllocator::parseTraceEntryAction转换；发布三参数入口没有该列表。未展开外部action字符串解析器的完整词表，不能编造任意别名。设置历史记录时enabled=False不等于清除保留块或重置所有内存统计。

## get_trace是在快照时合成

record_flag为False时返回空trace。非BUILD_LIBTORCH且开启时，每个现存stream块依次合成WORKSPACE_SNAPSHOT、SEGMENT_ALLOC、ALLOC三条，地址/尺寸均来自当前块；它们不是保留了所有历史申请和释放时间的事件日志。主线每条分别取getApproximateTime，携带MempoolId_t{0,0}和编译上下文字符串N/A，按skip_actions分别决定是否加入。合成条目不保留分配时compile context，不能用N/A推断实际未编译。

外层主线NpuWorkspaceAllocator持ApproximateClockToUnixTimeConverter，snapshot收集各设备get_trace/get_segm之后，通过makeConverter把每条approx_t转换为纳秒再除1000写入t_，得到epoch微秒。发布本文件没有这段显式转换，其TraceEntry采用较早签名；没有据此断言两版可直接按原始字段时间单位合并。时钟转换与事件生成时机需同时记录，不能将快照时刻当成原始分配时刻。

## SegmentInfo与allocated标志的边界

get_segm对每stream块合成一个segment：device/address/stream来自本地，is_large=True、is_expandable=False，含一个BlockInfo。total_size始终加block->size；allocated_size、active_size、requested_size只有block->allocated为真时才累加。WorkspaceBlock的allocated初值为0，完整本地实现没有把它置真；因此不能据segment中allocated/active为假就说该物理块不存在、未被kernel使用或整个设备没有活跃工作区。

block requested_size只在真正扩容申请成功后更新，缓存复用较小请求不刷新；segment里的这个字段不是每次最新算子的精确需求。get_trace的ALLOC合成与get_segm读取的allocated标志也不来自同一实时生命周期事件表，二者出现不同表象不能直接归咎于设备内存泄漏。

BUILD_LIBTORCH下get_trace/get_segm不生成这些记录，DeviceStats仍有本地统计路径；空快照不自动证明零分配。snapshot遍历设备依次收集，单设备内部锁不等于整个多设备的统一原子时间点。外层getDeviceStats校验device后返回copy，recordHistory对现有设备循环设置；初始化和调用顺序仍需保存。

解释内存图时记录编译构建分支、history开关/skip列表、实际缓存块和stream、快照生成时间及时间单位、逻辑统计与物理保留。本文记录局部源码口径，没有运行Profiler、构造快照或证明实际泄漏/无泄漏。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/NPUWorkspaceAllocator.cpp)（primary），读取范围 1–635。
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/NPUWorkspaceAllocator.h)（implementation），读取范围 1–46。
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/core/npu/NPUWorkspaceAllocator.cpp)（implementation），读取范围 1–617。
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/core/npu/NPUWorkspaceAllocator.h)（implementation），读取范围 1–42。
