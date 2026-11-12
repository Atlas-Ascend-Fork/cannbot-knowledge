---
type: Optimization
title: SGLang HiCache的MemFabric映射Host池与异步staging
description: 区分AIV可解引用的映射Host内存与普通pin-memory，说明首池固定reserve、MLA split/kernel_ascend条件、pinned事件保活与回退边界。
tags:
- task.optimization
- topic.kv_cache
- topic.memory
- topic.data_movement
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/mem_cache/pool_host/npu_memfabric.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/mem_cache/pool_host/mla.py
  role: implementation
created_at: '2026-11-08T11:53:43Z'
updated_at: '2026-11-09T04:35:53Z'
platforms: []
---

# SGLang HiCache的MemFabric映射Host池与异步staging

## 问题信号与优化规则

HiCache L2↔L1使用AIV sparse-copy Kernel时，普通torch pin-memory只供SDMA访问，不能据此认为AIV能解引用该Host虚拟地址。在 NPU 的 MLA split Host 池、layout=page_first_kv_split 前提下，SGLANG_HICACHE_HOST_MEM_BACKEND=memfabric 选择 memfabric_hybrid.offload.empty 分配的映射 Host 内存；只有 io_backend=kernel_ascend 且该 split 布局的读写分支才进一步进入 AscendC sparse-copy IO，不能推广到所有 HiCache 池/布局。该受限路径共用此开关；不能单独替换allocator或把普通pinned buffer交给该AIV路径。

## 容量和设备所有权

ensure_memfabric_capacity以首个Host池总字节配置LOCAL场景和GIANT_PAGE，initialize须返回0。进程只初始化一次，reserved_bytes固定为首次声明值，后续池必须放进剩余容量；代码没有自动增长或按不同设备建立独立reserve。底层可能向上整GiB预留，不能把请求字节当物理占用精确上限。

alloc_with_memfabric通过offload.empty分配，按numel*dtype.itemsize累加allocated_bytes；这里没有对应减计数/回收路径，不应推导释放一个Tensor后Python reserve账会自动恢复。--hicache-size/ratio不仅影响本池，也影响同进程后续池能否初始化。

## 避免Host上传暗同步

to_device_no_sync先将CPU Tensor pin_memory，分配device Tensor，再copy_(non_blocking=True)。track_pinned_staging在当前流记NPU Event并保存(pinned,event)，后续调用仅用event.query移除已完成项；不会主动synchronize整个stream。保活依赖记录事件与消费拷贝同一当前流，调用方必须保持这条顺序。

源码注释报告pageable.to/NPU tensor构造曾引入流同步，这是特定调用路径的动机，不是所有PyTorch版本的普遍时延定律。本次未重新profile。映射Host DRAM与pinned staging是两种不同用途的内存，不应混为一类“零拷贝”。

## 代价、回退与验证

先比Host reserve/allocated计数、实际进程DRAM与映射生命周期，再profileload/write流与compute是否重叠；记录TTFT/TPOT及缓存命中而不只看拷贝task。关闭env并重建Host池可回原IO，但不能在保留旧映射ptr的进程里混用两种allocator。验证事件保活、多个Host池、reserve耗尽和未安装MemFabric的明确失败。

## 证据与验证边界

本卡记录固定提交的NPU分支实现合同，来源没有为本机制提供完整产品验收矩阵，保留草稿和未定位平台；源码路径存在不证明任意昇腾型号可用。本次知识摄取未执行上游代码、编译、模型推理、真机、数值或性能测试。
