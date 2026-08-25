---
type: API
title: ReduceSum
description: 对多维向量按指定维度进行数据累加，通过pattern参数指定Reduce轴和Normal轴，当前支持AR和RA两种模式。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.reduction]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/reduction_operations/ReduceSum_interface/ReduceSum.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---


# ReduceSum

对多维向量按指定维度进行数据累加。定义指定计算维度为R轴，非指定维度为A轴。支持指定第一维或最后一维进行reduce。模板参数T支持half/float，pattern指定reduce模式。

提供两种重载：通过sharedTmpBuffer传入临时空间或由接口框架申请。临时空间大小通过GetReduceSumMaxMinTmpSize获取。模板参数isReuseSource预留（传false）。

接口参数：dstTensor输出；srcTensor输入；sharedTmpBuffer临时缓存；srcShape输入shape数组；srcInnerPad指示内轴是否已补齐。TPosition支持VECIN/VECCALC/VECOUT。

约束：遵循通用地址对齐约束。

<!-- cannbot:related:start -->
## 相关

- [Ascend950 ReduceSum AR 多行归约逐行错](../../../../../runbooks/precision/ascend950_reduce_sum_ar_multibundle_use_per_row.md)（`exemplifies`）：《Ascend950 ReduceSum AR 多行归约逐行错》说明Ascend950 上 ReduceSum<AR> 单次传入 aBundle>1 行时逐行结果错（总量近似但逐元素偏）；改逐行调用 ReduceSum(aBundle=1) 规避。仅当 aBundle>1 才触发。；《ReduceSum》说明对多维向量按指定维度进行数据累加，通过pattern参数指定Reduce轴和Normal轴，当前支持AR和RA两种模式。。二者在该故障专指ReduceSum AR一次处理多行时逐行错误，逐行调用、跨chunk累加和归约边界是直接修复/验证点上存在可执行的直接衔接。
- [Reduce count 必须排除 DMA 对齐填充元素](../../../../../runbooks/precision/reduction_count_excludes_dma_padding.md)（`exemplifies`）：Reduce count 必须排除 DMA 对齐填充元素 与《ReduceSum》的实质衔接是：DMA 对齐容量不是 Reduce 的数学 count；DataCopyPad/padding 故障、Softmax 与 ReduceMax/Sum 各层入口共同验证填充零经 Exp 后会污染分母。
- [int32 fp32累加reduce binary_equal不可达](../../../../../runbooks/precision/int32_fp32_reduce_binary_equal.md)（`exemplifies`）：《int32 fp32累加reduce binary_equal不可达》的任务是“int32 输入的 reduce 类算子内部 cast 到 fp32 累加，kernel 的 ReduceSum+bisection cache tree 与 golden 的 pairwise 折半是两棵不同 reduce 树；sum 超过 fp32 精确整数范围 2^24 时舍入路径不同致 1 ULP 差，cast 回 int32 后 bitwise 不一致，binary_equal 永不可达。”。《ReduceSum》具体提供“对多维向量按指定维度进行数据累加，通过pattern参数指定Reduce轴和Normal轴，当前支持AR和RA两种模式。”，它直接用于int32→fp32 ReduceSum 的规约树、有效 count 和 2^24 舍入边界。
- [CumSum接口](../../math_compute/cum_sum_interface/cum_sum_interface.md)（`related`）：ReduceSum 只输出归约结果，CumSum 保留每个前缀结果；二者按是否需要中间前缀直接选型。
- [GetReduceRepeatSumSpr](../../../basic_api/memory_vector_compute/reduction_compute_aux_config/get_reduce_repeat_sum_spr_isasi.md)（`related`）：GetReduceRepeatSumSpr 与《ReduceSum》的实质衔接是：GetReduceRepeatSumSpr 只读取前 n 连续 ReduceSum 的全局结果；ReduceSum 调用、临时空间和逐行/多 bundle 归约故障直接约束其使用。
- [ReduceSum](../../../basic_api/memory_vector_compute/reduction_compute/reduce_sum.md)（`related`）：Basic API ReduceSum 提供底层 UB 归约，高阶 ReduceSum 封装 shape/临时空间处理；二者解决同一求和归约但调用合同不同。
- [Sum](../sum_interface/sum.md)（`related`）：ReduceSum 与 Sum 的 shape/轴接口不同，应按所需输出契约选。
- [GetReduceSumMaxMinTmpSize](get_reduce_sum_max_min_tmp_size.md)（`same_topic`）：GetReduceSumMaxMinTmpSize 与《ReduceSum》的实质衔接是：该查询返回 ReduceSum 高阶实现所需的最大/最小临时空间；ReduceSum 入口消费这一预算，而多行、累加顺序和 binary_equal 案例给出实际归约验证边界。
- [ReduceSum接口](reduce_sum_interface.md)（`same_topic`）：函数页给出高阶 ReduceSum 的 axis、shape 与参数，是总览对应的实际调用。
- [Sum接口](../sum_interface/sum_interface.md)（`same_topic`）：Sum接口 与《ReduceSum》的实质衔接是：Sum 沿最后一维求和并由 GetSumMaxMinTmpSize 分配临时空间；ReduceSum 是可指定维度的相关入口，其空间查询与调用边界不同。
<!-- cannbot:related:end -->
