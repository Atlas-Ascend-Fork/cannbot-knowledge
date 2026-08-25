---
type: API
title: TCubeTiling结构体
description: TCubeTiling结构体包含Matmul Tiling切分算法的相关参数，被传递给Matmul Kernel侧，用于Matmul的切块、搬运和计算过程等。TCubeTiling结构体的参数说明见表1。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/cube_compute/Matmul_Tiling/TCubeTiling_struct.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# TCubeTiling结构体

头文件路径为："basic_api/kernel_operator_mm_intf.h"。 Mmad接口是Ascend C面向昇腾AI芯片的矩阵乘加核心计算接口，专为高性能算子开发设计，封装了昇腾NPU硬件的矩阵乘加计算能力，广泛用于神经网络层（如全连接层、卷积层）、数值计算类算子的开发。 Mmad接口实现昇腾NPU矩阵乘计算能力，其数学表达式为： 针对Ascend 950PR/Ascend 950DT：

本接口组包含 Mmad, 使用说明 及辅助接口 GetTiling, GetTiling。

约束：结果矩阵C只支持位于L0C Buffer（CO1），左矩阵A只支持位于L0A Buffer（A2），右矩阵B只支持位于L0B Buffer（B2）。；当M、K、N中的任意一个值为0时，表示指令不会执行，该接口将被视为NOP（空操作）。；当M = 1时，会默认开启GEMV（General Matrix-Vector Multiplication）功能。在这种情况下，Mmad API从L0A Buffer读取数据时，会以ND格式进行读取，而不会将其视为ZZ或NZ格式。所以此时左矩阵需要直接按照ND格式进行排布（GEMV特性说明）。要注意的是，开启GEMV的情况下，A矩阵的起始地址仍要求512字节对齐。；一般来说，一次Mmad计算至少完成一次A(16*16*half) * B(16*16*half)数据块计算。但实际计算时M、K、N有效值可能不是16的倍数，从而有部分数据为无效数据。以M=30，K=70，N=40为例来介绍无效数据与有效数据的排布方式。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。

<!-- cannbot:related:start -->
## 相关

- [Cube tile k/n 超 L1/L0 上限报 INVALID_TILE](../../../../../runbooks/compilation/cube_tile_k_n_l1_l0_invalid_tile.md)（`exemplifies`）：TCubeTiling结构体 与《Cube tile k/n 超 L1/L0 上限报 INVALID_TILE》的实质衔接是：TCubeTiling 由 GetTiling 生成、由 kernel 与空间查询消费；所选指南和越界卡解释字段配置与硬件 tile 上限。
- [Matmul高阶API开启MDL模板](../../../../../guides/operator_practice/best_practices/matmul_tuning_cases/matmul_mdl_template.md)（`explains`）：指南列出 MDL 的 singleCoreM/N/K、baseM/N/K、stepM/N/Ka/Kb 和 depthA1/B1，并要求同时满足 TCubeTiling 与 MDL 补充约束；TCubeTiling 卡承载 Kernel 切块、搬运和计算参数，是指南配置可执行性的直接数据合同。
- [使用高阶API时配套的Tiling实现](../../../../../guides/programming_guide/advanced_programming/aclnn_operator_development/design_and_implementation/tiling_with_advanced_api.md)（`explains`）：指南把 TCubeTiling 嵌入算子 TilingData 并传到 Kernel 初始化 Matmul；结构体卡定义这份切块、搬运和计算参数载体。
- [BatchMatmulGetTmpBufSize](../get_matmul_compute_space/batch_matmul_get_tmp_buf_size.md)（`related`）：《BatchMatmulGetTmpBufSize》处理“BatchMatmul Tiling调用GetTiling接口获取Tiling参数后，根据Tiling结构体信息获取L1 Buffer/Unified Buffer/L0C Buffer的使用大小。”。《TCubeTiling结构体》明确“TCubeTiling结构体包含Matmul Tiling切分算法的相关参数，被传递给Matmul Kernel侧，用于Matmul的切块、搬运和计算过程等。TCubeTiling结构体的参数说明见表1。”，可直接用于核对BatchMatmul 临时空间估算与 Matmul Tiling 对象、TCubeTiling 结果之间的调用合同。
- [EnableL1BankConflictOptimise](enable_l1_bank_conflict_optimise.md)（`related`）：EnableL1BankConflictOptimise 与《TCubeTiling结构体》的实质衔接是：该开关由 Matmul GetTiling 判定，随后写入 MatmulConfig 并通过新增 TilingKey 选择核侧分支；bank 规则和 key 位编码共同约束实现。
- [GetBaseK](get_base_k.md)（`related`）：BaseK 最终写入 TCubeTiling 并由 Kernel 消费。
- [Matmul Tiling类使用说明](matmul_tiling_usage.md)（`related`）：Host Matmul Tiling 的最终产物是 TCubeTiling，Kernel Init 消费该结构中的矩阵与分块参数。
- [SetDim](set_dim.md)（`related`）：《SetDim》的任务是“设置多核Matmul参与运算的核数，区分纯Cube模式和MIX模式的分离与耦合场景”。《TCubeTiling结构体》具体提供“TCubeTiling结构体包含Matmul Tiling切分算法的相关参数，被传递给Matmul Kernel侧，用于Matmul的切块、搬运和计算过程等。TCubeTiling结构体的参数说明见表1。”，它直接用于Matmul 核数、单核形状、split range 与最终 TCubeTiling 的一致性。
- [SetMadType](set_mad_type.md)（`related`）：《SetMadType》处理“设置是否开启HF32模式。当前版本暂不支持。 对于Ascend 950PR/Ascend 950DT，本接口可用于设置是否开启HF32模式（当前版本暂不支持）、设置是否开启MxMatmul场景。在MxMatmul场景，必须调用该接口并配置为开启MxMatmul场景，从而保证该场景下正确计算并返回Tiling参数。”。《TCubeTiling结构体》明确提供“TCubeTiling结构体包含Matmul Tiling切分算法的相关参数，被传递给Matmul Kernel侧，用于Matmul的切块、搬运和计算过程等。TCubeTiling结构体的参数说明见表1。”，其参数、调用或验证步骤直接接入Matmul 的 madType 配置、HF32/MxMatmul 模式及最终 Tiling 字段。
- [SetSingleRange](set_single_range.md)（`related`）：《SetSingleRange》处理“设置singleCoreM/singleCoreN/singleCoreK的最大值与最小值。”。《TCubeTiling结构体》明确“TCubeTiling结构体包含Matmul Tiling切分算法的相关参数，被传递给Matmul Kernel侧，用于Matmul的切块、搬运和计算过程等。TCubeTiling结构体的参数说明见表1。”，可直接用于核对Matmul Tiling 单范围/shape/split 参数写入、查询和最终 GetTiling 产出合同。
- [基础APIGEMV](../../../basic_api/cube_compute_tensor_api/mmad_compute_key_features/gemv.md)（`related`）：《基础APIGEMV》处理“GEMV的核心功能体现为：当矩阵A的维度M取值为1时，接口可以手动启用GEMV功能，该操作退化为1×K维度的行向量与K×N维度矩阵之间的乘法运算。”。《TCubeTiling结构体》明确提供“TCubeTiling结构体包含Matmul Tiling切分算法的相关参数，被传递给Matmul Kernel侧，用于Matmul的切块、搬运和计算过程等。TCubeTiling结构体的参数说明见表1。”，其参数、调用或验证步骤直接接入GEMV 的 Mmad 形状、行主序布局、对齐、Tiling 和结果验证。
- [GetBaseM](get_base_m.md)（`same_topic`）：GetBaseM 与《TCubeTiling结构体》的实质衔接是：baseM 与 baseN/baseK 一起写入 TCubeTiling，由输入 shape、single shape 与 GetTiling 计算；Matmul 使用说明解释该块大小如何驱动 kernel 循环。
- [GetSingleShape](get_single_shape.md)（`same_topic`）：GetSingleShape 与《TCubeTiling结构体》的实质衔接是：GetSingleShape 返回 GetTiling 计算出的单核 M/N/K，必须与 SetSingleShape/Range、baseM/N/K、coreNum 和 TCubeTiling 字段保持一致。
- [GetTiling](get_tiling.md)（`same_topic`）：TCubeTiling结构体 与《GetTiling》的实质衔接是：TCubeTiling 由 GetTiling 生成、由 kernel 与空间查询消费；所选指南和越界卡解释字段配置与硬件 tile 上限。
- [SetScaleAType](set_scale_a_type.md)（`same_topic`）：《SetScaleAType》处理“MxMatmul场景，设置scaleA矩阵的位置、数据格式、是否转置等信息，这些信息需要和Kernel侧的设置保持一致。如果不调用本接口，scaleA矩阵的信息将与SetAType中设置的A矩阵的信息保持一致。”。《TCubeTiling结构体》提供“TCubeTiling结构体包含Matmul Tiling切分算法的相关参数，被传递给Matmul Kernel侧，用于Matmul的切块、搬运和计算过程等。TCubeTiling结构体的参数说明见表1。”，其具体合同或探针直接接入MxMatmul 的 scaleA 位置/格式、Kernel scale 张量、搬运和 Mx 模式启用合同。
<!-- cannbot:related:end -->
