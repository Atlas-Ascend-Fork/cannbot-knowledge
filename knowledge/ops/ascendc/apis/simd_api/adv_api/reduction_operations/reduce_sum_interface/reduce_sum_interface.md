---
type: API
title: ReduceSum接口
description: 对多维向量在指定维度进行数据累加，并提供临时空间大小获取接口。
tags: [task.lookup, topic.compute.reduction]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/reduction_operations/ReduceSum_interface/ReduceSum_interface.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# ReduceSum接口

对多维向量在指定维度进行数据累加，并提供临时空间大小获取接口。

对一个多维向量按照指定的维度进行数据累加。 定义指定计算的维度（Reduce轴）为R轴，非指定维度（Normal轴）为A轴。如下图所示，对shape为(2, 3)的二维矩阵进行运算，指定在第一维计算数据的累加，输出结果为[5, 7, 9]；指定在第二维计算数据的累加，输出结果为[6, 15]。 图1 ReduceSum按第一个维度计算示例 图2 ReduceSum按最后一个维度计算示例

本接口组包含 ReduceSum。

本接口属于高阶归约运算接口。

约束：操作数地址对齐要求请参见通用地址对齐约束。；不支持源操作数与目的操作数地址重叠。；不支持sharedTmpBuffer与源操作数和目的操作数地址重叠。；内部算法不处理累加计算时的数据溢出，溢出场景不保证接口精度。

支持的硬件型号：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。

<!-- cannbot:related:start -->
## 相关

- [Ascend950 ReduceSum AR 多行归约逐行错](../../../../../runbooks/precision/ascend950_reduce_sum_ar_multibundle_use_per_row.md)（`exemplifies`）：《Ascend950 ReduceSum AR 多行归约逐行错》说明Ascend950 上 ReduceSum<AR> 单次传入 aBundle>1 行时逐行结果错（总量近似但逐元素偏）；改逐行调用 ReduceSum(aBundle=1) 规避。仅当 aBundle>1 才触发。；《ReduceSum接口》说明对多维向量在指定维度进行数据累加，并提供临时空间大小获取接口。。二者在该故障专指ReduceSum AR一次处理多行时逐行错误，逐行调用、跨chunk累加和归约边界是直接修复/验证点上存在可执行的直接衔接。
- [int32 fp32累加reduce binary_equal不可达](../../../../../runbooks/precision/int32_fp32_reduce_binary_equal.md)（`exemplifies`）：《int32 fp32累加reduce binary_equal不可达》的任务是“int32 输入的 reduce 类算子内部 cast 到 fp32 累加，kernel 的 ReduceSum+bisection cache tree 与 golden 的 pairwise 折半是两棵不同 reduce 树；sum 超过 fp32 精确整数范围 2^24 时舍入路径不同致 1 ULP 差，cast 回 int32 后 bitwise 不一致，binary_equal 永不可达。”。《ReduceSum接口》具体提供“对多维向量在指定维度进行数据累加，并提供临时空间大小获取接口。”，它直接用于int32→fp32 ReduceSum 的规约树、有效 count 和 2^24 舍入边界。
- [AscReduceSum](../../../c_api/reg/reduce_compute/asc_reduce_sum.md)（`related`）：Reg C API 在寄存器上完成求和，适合数据已驻留 RegTensor 的路径。
- [GetReduceRepeatSumSpr](../../../basic_api/memory_vector_compute/reduction_compute_aux_config/get_reduce_repeat_sum_spr_isasi.md)（`related`）：GetReduceRepeatSumSpr 与《ReduceSum接口》的实质衔接是：GetReduceRepeatSumSpr 只读取前 n 连续 ReduceSum 的全局结果；ReduceSum 调用、临时空间和逐行/多 bundle 归约故障直接约束其使用。
- [ReduceProd接口](../reduce_prod_interface/reduce_prod_interface.md)（`related`）：ReduceSum 与 ReduceProd 共享高阶归约框架但聚合运算不同，可按所需代数操作选型。
- [ReduceSum](../../../basic_api/memory_vector_compute/reduction_compute/reduce_sum.md)（`related`）：基础 Tensor ReduceSum 提供更低层归约，可按 shape 支持和临时空间需求与高阶接口选型。
- [ReduceXorSum接口](../reduce_xor_sum_interface/reduce_xor_sum_interface.md)（`related`）：普通 ReduceSum 做算术加法，XorSum 的聚合代数不同，不能互换。
- [GetReduceSumMaxMinTmpSize](get_reduce_sum_max_min_tmp_size.md)（`same_topic`）：GetReduceSumMaxMinTmpSize 与《ReduceSum接口》的实质衔接是：该查询返回 ReduceSum 高阶实现所需的最大/最小临时空间；ReduceSum 入口消费这一预算，而多行、累加顺序和 binary_equal 案例给出实际归约验证边界。
- [ReduceSum](reduce_sum.md)（`same_topic`）：函数页给出高阶 ReduceSum 的 axis、shape 与参数，是总览对应的实际调用。
- [Sum接口](../sum_interface/sum_interface.md)（`same_topic`）：Sum接口 与《ReduceSum接口》的实质衔接是：Sum 沿最后一维求和并由 GetSumMaxMinTmpSize 分配临时空间；ReduceSum 是可指定维度的相关入口，其空间查询与调用边界不同。
<!-- cannbot:related:end -->
