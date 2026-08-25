---
type: Guide
title: 多核对齐切分
description: 为了实现多核并行，提升计算效率，需要将矩阵数据进行切分，分配到不同的核上进行处理。主要的切分策略有切分K轴和不切分K轴两种。
tags: [task.lookup, topic.programming_model.execution_model.simd]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/operator_practice/simd_operator_impl/matrix_advanced_api/feature_scenarios/multi_core_aligned_split.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 多核对齐切分

## 功能介绍
为了实现多核并行，提升计算效率，需要将矩阵数据进行切分，分配到不同的核上进行处理。主要的切分策略有切分K轴和不切分K轴两种。
不切分K轴、仅切分M、N轴的策略如下：
-   对于A矩阵，沿着M轴进行切分，切分成多份的singleCoreM，单核上处理SingleCoreM * K大小的数据。
-   对于B矩阵，沿着N轴进行切分，切分成多份的singleCoreN，单核上处理K * SingleCoreN大小的数据。
-   对于C矩阵，SingleCoreM * K大小的A矩阵和K * SingleCoreN大小的B矩阵相乘得到SingleCoreM * SingleCoreN大小的C矩阵，即为单核上输出的C矩阵大小。
比如，下图中共有8个核参与计算，将A矩阵沿着M轴划分为4块，将B矩阵沿着N轴切分为两块，单核上仅处理某一分块（比如图中绿色部分为core5上参与计算的数据）：SingleCoreM * K大小的A矩阵分块和SingleCoreN * K大小的B矩阵分块相乘得到SingleCoreM * SingleCoreN大小的C矩阵分块。
切分M、N、K轴的策略如下图所示：
-   对于A矩阵，沿着M轴进行切分，切分成多份的singleCoreM，沿着K轴切分，切分成多份的singleCoreK，单核上处理singleCoreM * singleCoreK大小的数据。
-   对于B矩阵，沿着K轴进行切分，切分成多份的singleCoreK，沿着N轴进行切分，切分成多份的singleCoreN，单核上处理singleCoreK * singleCoreN大小的数据。
-   对于C矩阵，singleCoreM * singleCoreK大小的A矩阵与singleCoreK * singleCoreN大小的B矩阵相乘并累加得到singleCoreM * singleCoreN大小的C矩阵分块。
比如下图中，C矩阵中的R矩阵块，是通过A1*B1+A2*B2+A3*B3累加得到的，其中，A1*B1、A2*B2、A3*B3可在多个核上并行计算。
上述的切分策略会在Tiling参数中体现，比如SingleCoreM、SingleCoreN、SingleCoreK，开发者在host侧通过调用API自动获取Tiling参数，与单核场景的不同的是，多核Tiling需要使用MultiCoreMatmulTiling构造多核Tiling对象，并通过SetDim接口设置Matmul计算所用的核数。注意：这里设置的核数为Matmul计算可用的核数，仅在多核场景下设置，用于计算tiling参数；SetSimdNumBlocks为整个算子计算所用核数，是实际会加载的核数，是必须设置的。SetSimdNumBlocks的设置规则请参考numBlocks的说明。SetDim的设置规则如下：
-   纯Cube模式（只有矩阵计算）场景，本节内容以纯Cube模式举例。
SetDim设置当前AI处理器可用的核数，通过Tiling计算得到执行Matmul计算实际使用的核数，实际使用的核数小于等于AI处理器可用的核数。SetSimdNumBlocks按照实际使用的核数由用户进行配置。

<!-- cannbot:related:start -->
## 相关

- [EnableMultiCoreSplitK](../../../../../apis/simd_api/adv_api/cube_compute/matmul_tiling/enable_multi_core_split_k.md)（`explains`）：多核对齐切分 与《EnableMultiCoreSplitK》的实质衔接是：对齐切分按可用核数设置 SetDim/NumBlocks，并与非对齐尾块、N 对齐、Channel 拆分、多核 K 切分及临时空间计算共同决定实际 Matmul 分工。
- [MultiCoreMatmulGetTmpBufSize](../../../../../apis/simd_api/adv_api/cube_compute/get_matmul_compute_space/multi_core_matmul_get_tmp_buf_size.md)（`explains`）：多核对齐切分 与《MultiCoreMatmulGetTmpBufSize》的实质衔接是：对齐切分按可用核数设置 SetDim/NumBlocks，并与非对齐尾块、N 对齐、Channel 拆分、多核 K 切分及临时空间计算共同决定实际 Matmul 分工。
- [MultiCoreMatmulGetTmpBufSizeV2](../../../../../apis/simd_api/adv_api/cube_compute/get_matmul_compute_space/multi_core_matmul_get_tmp_buf_size_v2.md)（`explains`）：多核对齐切分 与《MultiCoreMatmulGetTmpBufSizeV2》的实质衔接是：对齐切分按可用核数设置 SetDim/NumBlocks，并与非对齐尾块、N 对齐、Channel 拆分、多核 K 切分及临时空间计算共同决定实际 Matmul 分工。
- [NumBlocks](../../../../../apis/simt_api/cooperative_groups/grid_group/num_blocks.md)（`explains`）：多核对齐切分 与《NumBlocks》的实质衔接是：对齐切分按可用核数设置 SetDim/NumBlocks，并与非对齐尾块、N 对齐、Channel 拆分、多核 K 切分及临时空间计算共同决定实际 Matmul 分工。
- [SetDim](../../../../../apis/simd_api/adv_api/cube_compute/matmul_tiling/set_dim.md)（`explains`）：《SetDim》的任务是“设置多核Matmul参与运算的核数，区分纯Cube模式和MIX模式的分离与耦合场景”。《多核对齐切分》具体提供“为了实现多核并行，提升计算效率，需要将矩阵数据进行切分，分配到不同的核上进行处理。主要的切分策略有切分K轴和不切分K轴两种。”，它直接用于Matmul 核数、单核形状、split range 与最终 TCubeTiling 的一致性。
- [FindSplitAxis 误传 total_slots 致 slot 翻倍](../../../../../runbooks/precision/findsplitaxis_total_slots_slot.md)（`related`）：FindSplitAxis 误传 total_slots 致 slot 翻倍 与《多核对齐切分》的实质衔接是：FindSplitAxis 第四参要求 phys_nodes，传入已乘 DB 的 total_slots 会再次乘二；per-buffer UB 预算、rank/split、TilingData 和 Broadcast 卡用于核对内外切分量一致。
- [Matmul特性介绍](matmul_features.md)（`same_topic`）：多核对齐切分 与《Matmul特性介绍》的实质衔接是：对齐切分按可用核数设置 SetDim/NumBlocks，并与非对齐尾块、N 对齐、Channel 拆分、多核 K 切分及临时空间计算共同决定实际 Matmul 分工。
- [Matmul高阶API开启多核K轴错峰访问内存](../../../best_practices/matmul_tuning_cases/matmul_multi_core_k_stagger.md)（`same_topic`）：多核对齐切分 与《Matmul高阶API开启多核K轴错峰访问内存》的实质衔接是：对齐切分按可用核数设置 SetDim/NumBlocks，并与非对齐尾块、N 对齐、Channel 拆分、多核 K 切分及临时空间计算共同决定实际 Matmul 分工。
- [Matmul高阶API开启多核切K](../../../best_practices/matmul_tuning_cases/matmul_multi_core_split_k.md)（`same_topic`）：多核对齐切分 与《Matmul高阶API开启多核切K》的实质衔接是：对齐切分按可用核数设置 SetDim/NumBlocks，并与非对齐尾块、N 对齐、Channel 拆分、多核 K 切分及临时空间计算共同决定实际 Matmul 分工。
- [单次矩阵乘局部输出](single_matmul_local_output.md)（`same_topic`）：多核对齐切分 与《单次矩阵乘局部输出》的实质衔接是：对齐切分按可用核数设置 SetDim/NumBlocks，并与非对齐尾块、N 对齐、Channel 拆分、多核 K 切分及临时空间计算共同决定实际 Matmul 分工。
- [多核非对齐切分](multi_core_unaligned_split.md)（`same_topic`）：多核对齐切分 与《多核非对齐切分》的实质衔接是：对齐切分按可用核数设置 SetDim/NumBlocks，并与非对齐尾块、N 对齐、Channel 拆分、多核 K 切分及临时空间计算共同决定实际 Matmul 分工。
- [矩阵乘输出的Channel拆分](matmul_output_channel_split.md)（`same_topic`）：多核对齐切分 与《矩阵乘输出的Channel拆分》的实质衔接是：对齐切分按可用核数设置 SetDim/NumBlocks，并与非对齐尾块、N 对齐、Channel 拆分、多核 K 切分及临时空间计算共同决定实际 Matmul 分工。
- [矩阵乘输出的N方向对齐](matmul_output_n_alignment.md)（`same_topic`）：多核对齐切分 与《矩阵乘输出的N方向对齐》的实质衔接是：对齐切分按可用核数设置 SetDim/NumBlocks，并与非对齐尾块、N 对齐、Channel 拆分、多核 K 切分及临时空间计算共同决定实际 Matmul 分工。
<!-- cannbot:related:end -->
