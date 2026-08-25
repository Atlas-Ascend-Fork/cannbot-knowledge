---
type: Guide
title: 设置合理的L2 CacheMode
description: '>该性能优化指导适用于如下产品型号：'
tags: [task.lookup, topic.performance.optimization.optimization_overview]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/operator_practice/simd_operator_optimization/memory_access/l2_cache_mode_config.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# 设置合理的L2 CacheMode

【优先级】高
【描述】L2 Cache常用于缓存频繁访问的数据，其物理位置如下图所示：
L2 Cache的带宽相比GM的带宽有数倍的提升，因此当数据命中L2 Cache时，数据的搬运耗时会优化数倍。通常情况下，L2 Cache命中率越高，算子的性能越好，在实际访问中需要通过设置合理的L2 CacheMode来保证重复读取的数据尽量缓存在L2 Cache上。
## L2 Cache访问的原理及CacheMode介绍
数据通过MTE2搬运单元搬入时，L2 Cache访问的典型流程如下：
数据通过MTE3或者Fixpipe搬运单元搬出时，L2 Cache访问的典型流程如下：
从上面的流程可以看出，当数据访问总量超出L2 Cache容量时，AI Core会对L2 Cache进行数据替换。由于Cache一致性的要求，替换过程中旧数据需要先写回GM（此过程中会占用GM带宽），旧数据写回后，新的数据才能进入L2 Cache。
开发者可以针对访问的数据设置其CacheMode，对于只访问一次的Global Memory数据设置其访问状态为不进入L2 Cache，这样可以更加高效的利用L2 Cache缓存需要重复读取的数据，避免一次性访问的数据替换有效数据。
## 设置L2 CacheMode的方法
Ascend C基于GlobalTensor提供了SetL2CacheHint接口，用户可以根据需要指定CacheMode。
考虑如下场景，构造两个Tensor的相加计算，输入x、y和输出z的Shape均为(8192, 8192)。下文完整样例请参考设置合理L2 CacheMode样例。

<!-- cannbot:related:start -->
## 相关

- [AscLdca](../../../../apis/simt_api/memory_access_functions/asc_ldca.md)（`explains`）：L2 CacheMode 指南解释 Ldca 命中顺序和 mode 对缓存分配的影响。
- [AscLoadL2CacheMode](../../../../apis/simd_api/c_api/enum/asc_load_l2_cache_mode.md)（`explains`）：AscLoadL2CacheMode说明表示数据从GM搬运到UB时的L2 cache管理策略，在调用asc_copy_gm2ub_align和asc_ndim_copy_gm2ub时使用。
- [AscStoreL2CacheMode](../../../../apis/simd_api/c_api/enum/asc_store_l2_cache_mode.md)（`explains`）：AscStoreL2CacheMode说明表示数据从UB搬运到GM时的L2 cache策略，在调用asc_copy_ub2gm_align时使用。
- [SetL2CacheHint](../../../../apis/simd_api/basic_api/data_structures/global_tensor/set_l2_cache_hint.md)（`explains`）：The guide explains why one-shot tensors may disable L2 while reused tensors should remain cached, and shows SetL2CacheHint as the control point.
- [asc_ldcg（内存访问函数）](../../../../apis/simt_api/memory_access_functions/asc_ldcg.md)（`explains`）：asc_ldcg（内存访问函数） 与《设置合理的L2 CacheMode》的实质衔接是：asc_ldcg 通过 L2 cache 读取 GM，stcg 是写回配对，DCCI 用于失效缓存；L2 模式和 Scalar 访存指南共同决定命中策略与一致性。
- [asc_stcg（内存访问函数）](../../../../apis/simt_api/memory_access_functions/asc_stcg.md)（`explains`）：L2 mode 指南解释 Stcg 写入 L2 的行为和适用场景。
- [asc_stwt（内存访问函数）](../../../../apis/simt_api/memory_access_functions/asc_stwt.md)（`explains`）：asc_stwt（内存访问函数） 与《设置合理的L2 CacheMode》的实质衔接是：asc_stwt 把数据写入 GM 并缓存到 DCache/L2；stcg/ldcg、缓存模式和 DCCI 共同决定写策略、后续读取及显式失效时机。
- [矩阵搬出寄存器配置说明](../../../../apis/simd_api/basic_api/cube_compute/cube_store_aux_config/cube_store_aux_config.md)（`explains`）：矩阵搬出寄存器配置说明 与《设置合理的L2 CacheMode》的实质衔接是：矩阵搬出配置寄存器在核内持久，SetFixPipeConfig/NZ2ND/Addr/Relu/PreQuant 控制 Fixpipe 搬出；量化、ReLU、L2 和格式转换材料说明各状态的真实效果。
- [Ascend950 DataCopy 写回 L2 驱逐丢对角线](../../../../runbooks/precision/ascend950_datacopy_l2.md)（`related`）：Ascend950 DataCopy 写回 L2 驱逐丢对角线说明Ascend950 上 fill_diagonal_v2 dense path 用 DataCopy 批量写回整个 tile 到 GM 时写入经多核共享 L2 cache，64 核并行写入合计约 8MB 超出 L2 容量，后 32 核 dirty cache line 在末尾 DataCacheCleanAndInvalid 前被驱逐未刷回 GM，对角线位置丢失；判别方法为 dump 比对定位对角线 out==input 且分界线落核 31/32 与 4MB L2 临界点一致。
- [L2 读写端口独立并行 HBM 总线串行共享](../../../../runbooks/performance/l2_hbm.md)（`related`）：《L2 读写端口独立并行 HBM 总线串行共享》处理“Ascend950 L2 的 MTE2 读端口与 MTE3 写端口独立并行（吞吐可相加），HBM 总线被读写共享串行仲裁；并发读写带宽应按总数据量与实际并发时间算，不能把单路带宽相加当并发带宽。”。《设置合理的L2 CacheMode》明确提供“>该性能优化指导适用于如下产品型号：”，其参数、调用或验证步骤直接接入L2 读写路径的 cache 控制、带宽、端口争用和 fence 验证。
- [L2CacheSplit](l2_cache_split.md)（`related`）：L2CacheSplit 与《设置合理的L2 CacheMode》的衔接是：大数据 L2CacheSplit 的分块策略由 Matmul L2 split 案例落地，L2 hint 与 load/store cache mode 决定分块数据是否按预期进入和复用 L2。
- [Matmul高阶API开启L2 Cache切分](../../best_practices/matmul_tuning_cases/matmul_l2_cache_split.md)（`same_topic`）：Matmul高阶API开启L2 Cache切分说明本案例呈现了在Matmul计算过程中，输入和输出的数据总量超过L2 Cache大小时，通过L2 Cache数据切分对算子性能的提升效果。开启L2 Cache切分的完整样例请参考L2 Cache切分的算子样例。
<!-- cannbot:related:end -->
