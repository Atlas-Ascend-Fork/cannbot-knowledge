---
type: Guide
title: Batch Matmul基础功能
description: Batch Matmul是指批量处理Matmul计算的场景。该场景对外提供了IterateBatch的调用接口，调用一次IterateBatch，可以计算出多个singleCoreM
  \ singleCoreN大小的C矩阵。
tags: [task.lookup, topic.programming_model.execution_model.simd]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/operator_practice/simd_operator_impl/matrix_advanced_api/feature_scenarios/batch_matmul_basics.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# Batch Matmul基础功能

## 功能介绍
Batch Matmul是指批量处理Matmul计算的场景。该场景对外提供了IterateBatch的调用接口，调用一次IterateBatch，可以计算出多个singleCoreM * singleCoreN大小的C矩阵。
Matmul单次计算的过程需要搬入和搬出数据，当进行多次Matmul计算且单次Matmul计算的输入shape较小时，搬运开销在整体耗时中占比较大。通过IterateBatch接口批量处理Matmul，可以有效提升带宽利用率。
Batch Matmul当前支持4种Layout类型：BSNGD、SBNGD、BNGS1S2、NORMAL（BMNK的数据排布格式），相关数据排布格式请参考IterateBatch。
下图为NORMAL数据排布格式的Batch Matmul计算。整个Matmul计算一共包含4个矩阵乘操作：mat_a1*mat_b1、mat_a2*mat_b2、mat_a3*mat_b3、mat_a4*mat_b4，需要单核上计算四个singleCoreM *singleCoreN。在该场景下，如果shape较小，可以将其视为Batch Matmul场景进行批量处理，以提升性能。一次IterateBatch可同时计算出mat_c1 = mat_a1 * mat_b1、mat_c2 = mat_a2 * mat_b2、mat_c3 = mat_a3 * mat_b3、mat_c4 = mat_a4 * mat_b4。
## 使用场景
Matmul计算需要计算出多个singleCoreM * singleCoreN大小的C矩阵，且单次Matmul计算处理的shape较小。
## 约束说明
-   只支持Norm模板。
-   对于BSNGD、SBNGD、BNGS1S2 Layout格式，输入A、B矩阵按分形对齐后的多Batch数据总和应小于L1 Buffer的大小；对于NORMAL Layout格式没有这种限制，但需通过MatmulConfig配置batchMode参数，即输入A、B矩阵多Batch数据大小与L1 Buffer的大小关系；
-   对于BSNGD、SBNGD、BNGS1S2 Layout格式，称左矩阵、右矩阵的G轴分别为ALayoutInfoG、BLayoutInfoG，则ALayoutInfoG / batchA = BLayoutInfoG / batchB；对于NORMAL Layout格式，batchA 、batchB必须满足倍数关系。Bias的shape(batch, n)中的batch必须与C矩阵的batch相等。
-   如果接口输出到Unified Buffer上，输出C矩阵大小BaseM*BaseN应小于分配的Unified Buffer内存大小。
-   对于BSNGD、SBNGD Layout格式，输入输出只支持ND格式数据。对于BNGS1S2、NORMAL Layout格式，输入支持ND/NZ格式数据。
-   Batch Matmul不支持量化/反量化模式，即不支持SetQuantScalar、SetQuantVector接口。

<!-- cannbot:related:start -->
## 相关

- [BatchMatmulGetTmpBufSize](../../../../../apis/simd_api/adv_api/cube_compute/get_matmul_compute_space/batch_matmul_get_tmp_buf_size.md)（`explains`）：《BatchMatmulGetTmpBufSize》处理“BatchMatmul Tiling调用GetTiling接口获取Tiling参数后，根据Tiling结构体信息获取L1 Buffer/Unified Buffer/L0C Buffer的使用大小。”。《Batch Matmul基础功能》明确“Batch Matmul是指批量处理Matmul计算的场景。该场景对外提供了IterateBatch的调用接口，调用一次IterateBatch，可以计算出多个singleCoreM \ singleCoreN大小的C矩阵。”，可直接用于核对BatchMatmul 临时空间估算与 Matmul Tiling 对象、TCubeTiling 结果之间的调用合同。
- [BatchMatmulGetTmpBufSizeV2](../../../../../apis/simd_api/adv_api/cube_compute/get_matmul_compute_space/batch_matmul_get_tmp_buf_size_v2.md)（`explains`）：Batch Matmul基础功能 与《BatchMatmulGetTmpBufSizeV2》的实质衔接是：Batch Matmul 直接使用 Batch tmp 查询、IterateBatch/NBatch、batch shape/输出与 batch 数配置；workspace 和精度卡约束真实使用。
- [GetBatchC](../../../../../apis/simd_api/adv_api/cube_compute/matmul_kernel/get_batch_c.md)（`explains`）：Batch Matmul基础功能 与《GetBatchC》的实质衔接是：Batch Matmul 直接使用 Batch tmp 查询、IterateBatch/NBatch、batch shape/输出与 batch 数配置；workspace 和精度卡约束真实使用。
- [GetBatchTensorC](../../../../../apis/simd_api/adv_api/cube_compute/matmul_kernel/get_batch_tensor_c.md)（`explains`）：GetBatchTensorC 与《Batch Matmul基础功能》的实质衔接是：GetBatchTensorC 只在 IterateNBatch 异步输出链中取回一片 batch C；Host batch 配置、workspace 和 WaitIterateBatch 决定该取回路径的形状与同步方式。
- [IterateBatch](../../../../../apis/simd_api/adv_api/cube_compute/matmul_kernel/iterate_batch.md)（`explains`）：Batch Matmul基础功能 与《IterateBatch》的实质衔接是：Batch Matmul 直接使用 Batch tmp 查询、IterateBatch/NBatch、batch shape/输出与 batch 数配置；workspace 和精度卡约束真实使用。
- [IterateNBatch](../../../../../apis/simd_api/adv_api/cube_compute/matmul_kernel/iterate_n_batch.md)（`explains`）：Batch Matmul基础功能 与《IterateNBatch》的实质衔接是：Batch Matmul 直接使用 Batch tmp 查询、IterateBatch/NBatch、batch shape/输出与 batch 数配置；workspace 和精度卡约束真实使用。
- [SetBatchInfoForNormal](../../../../../apis/simd_api/adv_api/cube_compute/matmul_tiling/set_batch_info_for_normal.md)（`explains`）：Batch Matmul基础功能 与《SetBatchInfoForNormal》的实质衔接是：Batch Matmul 直接使用 Batch tmp 查询、IterateBatch/NBatch、batch shape/输出与 batch 数配置；workspace 和精度卡约束真实使用。
- [SetBatchNum](../../../../../apis/simd_api/adv_api/cube_compute/matmul_tiling/set_batch_num.md)（`explains`）：Batch Matmul基础功能 与《SetBatchNum》的实质衔接是：Batch Matmul 直接使用 Batch tmp 查询、IterateBatch/NBatch、batch shape/输出与 batch 数配置；workspace 和精度卡约束真实使用。
- [Batch Matmul复用Bias矩阵](batch_matmul_reuse_bias.md)（`related`）：Bias 复用建立在 Batch Matmul 基本 shape/batch 配置上，只在各 batch 使用同一 Bias 时将 isBiasBatch 设 false。
- [Matmul workspace 预偏移 totalN 回读 banned](../../../../../runbooks/precision/matmul_workspace_totaln_banned.md)（`related`）：Batch Matmul基础功能 与《Matmul workspace 预偏移 totalN 回读 banned》的实质衔接是：Batch Matmul 直接使用 Batch tmp 查询、IterateBatch/NBatch、batch shape/输出与 batch 数配置；workspace 和精度卡约束真实使用。
- [含有Matmul高阶API的算子精度问题](../../../../programming_guide/appendix/faq/matmul_advanced_api_precision.md)（`related`）：Batch Matmul基础功能 与《含有Matmul高阶API的算子精度问题》的实质衔接是：Batch Matmul 直接使用 Batch tmp 查询、IterateBatch/NBatch、batch shape/输出与 batch 数配置；workspace 和精度卡约束真实使用。
<!-- cannbot:related:end -->
