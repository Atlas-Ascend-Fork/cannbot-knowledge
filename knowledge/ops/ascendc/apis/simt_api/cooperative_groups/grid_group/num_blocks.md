---
type: API
title: NumBlocks
description: 获取当前Grid内的线程块总数。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.programming_model.cooperative_groups]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/cooperative_groups/grid_group/num_blocks.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# NumBlocks

获取当前Grid内的线程块总数。
函数原型：static unsigned long long num_blocks()
返回值：当前Grid内的线程块总数。
约束：仅支持SIMT编程场景，不支持SIMD与SIMT混合编程场景。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [block 数应覆盖可用 Vector 核](../../../../runbooks/performance/block_count_uses_all_available_vector_cores.md)（`exemplifies`）：block 数应覆盖可用 Vector 核说明Host 的固定 block 上限低于目标设备实测 Vector Core 数；把上限绑定到同设备探针结果后，配对端到端性能改善且正确性未退化。
- [blockLength 对齐 slice 致 numBlocks 塌缩单核](../../../../runbooks/performance/blocklength_slice_numblocks.md)（`exemplifies`）：blockLength 对齐 slice 致 numBlocks 塌缩单核说明SwiGlu host tiling 把 blockLength 对齐到 slice 边界后，当 totalSlices < coreNum（极端 totalSlices=1）时 numBlocks=min(coreNum,totalSlices/minSlicesPerCore) 塌缩为 1，整 block 串行单核，大 shape case 退化约一个数量级；判别方法：对齐版大 slice case 成对耗时远高于不对齐版即命中。
- [每核最少行数地板压低 AIV 并行度—按可用核数切分](../../../../runbooks/performance/row_reduction_min_rows_floor_underutilizes_aiv.md)（`exemplifies`）：每核最少行数地板压低 AIV 并行度—按可用核数切分说明行级归约 tiling 不应先用每核最少行数限制 block 数；按可用 AIV 核数上限切分可恢复并行度。
- [多核对齐切分](../../../../guides/operator_practice/simd_operator_impl/matrix_advanced_api/feature_scenarios/multi_core_aligned_split.md)（`explains`）：多核对齐切分 与《NumBlocks》的实质衔接是：对齐切分按可用核数设置 SetDim/NumBlocks，并与非对齐尾块、N 对齐、Channel 拆分、多核 K 切分及临时空间计算共同决定实际 Matmul 分工。
- [BlockRank](block_rank.md)（`related`）：NumBlocks 给出 rank 的上界，可用于校验 BlockRank 是否落在 [0,num_blocks)。
- [CalcTschNumBlocks](../../../utils_api/platform_info/platform_ascend_c/calc_tsch_num_blocks.md)（`related`）：CalcTschNumBlocks说明针对Cube与Vector分离模式，计算融合算子启动的numBlocks值，即AIV与AIC组合数量，结果通过SetSimdNumBlocks设置。
- [DimBlocks](dim_blocks.md)（`related`）：DimBlocks说明获取当前Grid的线程块维度配置。
- [GroupDim](group_dim.md)（`related`）：“GroupDim”定义：获取当前Grid的线程块维度配置，与接口dim_blocks功能相同。；“NumBlocks”定义：获取当前Grid内的线程块总数。。实质衔接：GroupDim 与 DimBlocks 返回同一 Grid 三维块配置，NumBlocks 将三维配置折叠为总块数；grid_group 说明对象获取与作用域。
- [NumThreads](num_threads.md)（`related`）：NumThreads：grid_group 的 NumThreads 与 size共同给出网格总线程数，ThreadRank据此界定合法索引，GroupDim/NumBlocks说明总数的分解，构造函数提供对象来源。 目标卡《NumBlocks》补充：获取当前Grid内的线程块总数。
- [ThreadRank](thread_rank.md)（`same_topic`）：ThreadRank：grid_group ThreadRank以NumThreads/size为上界，BlockRank/BlockIndex与GroupDim/NumBlocks解释全局rank分解，构造函数给出group对象来源。 目标卡《NumBlocks》补充：获取当前Grid内的线程块总数。
<!-- cannbot:related:end -->
