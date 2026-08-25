---
type: API
title: GetReduceSumMaxMinTmpSize
description: 在host侧获取ReduceSum接口所需的最大和最小临时空间大小，当前最大值等于最小值，供开发者选择Tiling参数。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.reduction]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/reduction_operations/ReduceSum_interface/GetReduceSumMaxMinTmpSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---


# GetReduceSumMaxMinTmpSize

host侧Tiling接口，用于获取ReduceSum接口所需的最大和最小临时空间大小，开发者据此选择合适的Tiling参数传入kernel侧。

函数原型：void GetReduceSumMaxMinTmpSize(const AscendC::TensorShape& srcShape, const uint32_t typeSize, const bool isReuseSource, uint32_t& maxValue, uint32_t& minValue)

参数：srcShape为输入shape；typeSize为数据类型字节数（half传2）；isReuseSource与ReduceSum接口保持一致；maxValue输出最大临时空间大小（超出不被使用，为0表示无需临时空间，可能大于Unified Buffer剩余空间）；minValue输出最小临时空间大小（实际预留不能小于该值，为0表示无需临时空间）。

在minValue到maxValue范围内，临时空间越大性能越好。约束：无。

<!-- cannbot:related:start -->
## 相关

- [Ascend950 ReduceSum AR 多行归约逐行错](../../../../../runbooks/precision/ascend950_reduce_sum_ar_multibundle_use_per_row.md)（`exemplifies`）：《Ascend950 ReduceSum AR 多行归约逐行错》说明Ascend950 上 ReduceSum<AR> 单次传入 aBundle>1 行时逐行结果错（总量近似但逐元素偏）；改逐行调用 ReduceSum(aBundle=1) 规避。仅当 aBundle>1 才触发。；《GetReduceSumMaxMinTmpSize》说明在host侧获取ReduceSum接口所需的最大和最小临时空间大小，当前最大值等于最小值，供开发者选择Tiling参数。。二者在该故障专指ReduceSum AR一次处理多行时逐行错误，逐行调用、跨chunk累加和归约边界是直接修复/验证点上存在可执行的直接衔接。
- [int32 fp32累加reduce binary_equal不可达](../../../../../runbooks/precision/int32_fp32_reduce_binary_equal.md)（`exemplifies`）：《int32 fp32累加reduce binary_equal不可达》的任务是“int32 输入的 reduce 类算子内部 cast 到 fp32 累加，kernel 的 ReduceSum+bisection cache tree 与 golden 的 pairwise 折半是两棵不同 reduce 树；sum 超过 fp32 精确整数范围 2^24 时舍入路径不同致 1 ULP 差，cast 回 int32 后 bitwise 不一致，binary_equal 永不可达。”。《GetReduceSumMaxMinTmpSize》具体提供“在host侧获取ReduceSum接口所需的最大和最小临时空间大小，当前最大值等于最小值，供开发者选择Tiling参数。”，它直接用于int32→fp32 ReduceSum 的规约树、有效 count 和 2^24 舍入边界。
- [大归约维 fp32 golden 顺序累加致假精度失败](../../../../../runbooks/precision/fp32_golden.md)（`exemplifies`）：GetReduceSumMaxMinTmpSize 与《大归约维 fp32 golden 顺序累加致假精度失败》的实质衔接是：该查询返回 ReduceSum 高阶实现所需的最大/最小临时空间；ReduceSum 入口消费这一预算，而多行、累加顺序和 binary_equal 案例给出实际归约验证边界。
- [GetReduceRepeatSumSpr](../../../basic_api/memory_vector_compute/reduction_compute_aux_config/get_reduce_repeat_sum_spr_isasi.md)（`related`）：GetReduceRepeatSumSpr 与《GetReduceSumMaxMinTmpSize》的实质衔接是：GetReduceRepeatSumSpr 只读取前 n 连续 ReduceSum 的全局结果；ReduceSum 调用、临时空间和逐行/多 bundle 归约故障直接约束其使用。
- [ReduceSum](reduce_sum.md)（`same_topic`）：GetReduceSumMaxMinTmpSize 与《ReduceSum》的实质衔接是：该查询返回 ReduceSum 高阶实现所需的最大/最小临时空间；ReduceSum 入口消费这一预算，而多行、累加顺序和 binary_equal 案例给出实际归约验证边界。
- [ReduceSum接口](reduce_sum_interface.md)（`same_topic`）：GetReduceSumMaxMinTmpSize 与《ReduceSum接口》的实质衔接是：该查询返回 ReduceSum 高阶实现所需的最大/最小临时空间；ReduceSum 入口消费这一预算，而多行、累加顺序和 binary_equal 案例给出实际归约验证边界。
- [Sum接口](../sum_interface/sum_interface.md)（`same_topic`）：Sum接口 与《GetReduceSumMaxMinTmpSize》的实质衔接是：Sum 沿最后一维求和并由 GetSumMaxMinTmpSize 分配临时空间；ReduceSum 是可指定维度的相关入口，其空间查询与调用边界不同。
<!-- cannbot:related:end -->
