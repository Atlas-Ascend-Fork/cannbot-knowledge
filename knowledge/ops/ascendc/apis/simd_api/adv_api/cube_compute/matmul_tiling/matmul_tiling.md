---
type: API
title: Matmul Tiling类
description: 提供Matmul矩阵乘的Host侧Tiling类，包含TCubeTiling结构体、GetTiling及形状、类型、切分等参数设置方法。
tags: [task.lookup, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/cube_compute/Matmul_Tiling/Matmul_Tiling.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# Matmul Tiling类

提供矩阵乘计算的 Host 侧 Tiling 类，通过 TCubeTiling 结构体承载切分参数。
核心方法 GetTiling 获取最终 Tiling 数据；SetAType/SetBType/SetCType/SetBiasType 设置各矩阵数据类型，SetSingleShape/SetShape/SetOrgShape 设置形状参数，SetALayout/SetBLayout/SetCLayout 设置排布格式。
切分控制方法包括 SetFixSplit、EnableMultiCoreSplitK、SetSplitK、SetSplitRange、SetDoubleBuffer 等；GetBaseM/GetBaseN/GetBaseK 查询基础分块大小，GetCoreNum 查询核数。
另支持 EnableBias、SetMadType、SetDequantType、SetSparse 等特性开关。

<!-- cannbot:related:start -->
## 相关

- [Matmul算子优化Tiling策略](../../../../../guides/operator_practice/best_practices/matmul_tuning_cases/matmul_tiling_strategy.md)（`explains`）：调优页说明如何据 shape/资源选择切分策略。
- [使用高阶API时配套的Tiling实现](../../../../../guides/programming_guide/advanced_programming/aclnn_operator_development/design_and_implementation/tiling_with_advanced_api.md)（`explains`）：指南使用的 MultiCoreMatmulTiling/TCubeTiling 流程属于 Matmul Host Tiling 类；目标总览把 SetA/B/CType、形状设置、切分控制和 GetTiling 串成同一接口对象。
- [BatchMatmulGetTmpBufSize](../get_matmul_compute_space/batch_matmul_get_tmp_buf_size.md)（`related`）：《BatchMatmulGetTmpBufSize》处理“BatchMatmul Tiling调用GetTiling接口获取Tiling参数后，根据Tiling结构体信息获取L1 Buffer/Unified Buffer/L0C Buffer的使用大小。”。《Matmul Tiling类》明确“提供Matmul矩阵乘的Host侧Tiling类，包含TCubeTiling结构体、GetTiling及形状、类型、切分等参数设置方法。”，可直接用于核对BatchMatmul 临时空间估算与 Matmul Tiling 对象、TCubeTiling 结果之间的调用合同。
- [EnableMultiCoreSplitK](enable_multi_core_split_k.md)（`related`）：SplitK 是总 tiling 流程中的多核策略分支。
- [SetAType](set_a_type.md)（`related`）：SetAType 与《Matmul Tiling类》的实质衔接是：SetB/SetA 类型、MatmulTiling 构造与 kernel 的 SetTensorA 共同约束矩阵位置、格式、dtype、转置在 host/kernel 两侧一致。
- [SetMadType](set_mad_type.md)（`related`）：《SetMadType》处理“设置是否开启HF32模式。当前版本暂不支持。 对于Ascend 950PR/Ascend 950DT，本接口可用于设置是否开启HF32模式（当前版本暂不支持）、设置是否开启MxMatmul场景。在MxMatmul场景，必须调用该接口并配置为开启MxMatmul场景，从而保证该场景下正确计算并返回Tiling参数。”。《Matmul Tiling类》明确提供“提供Matmul矩阵乘的Host侧Tiling类，包含TCubeTiling结构体、GetTiling及形状、类型、切分等参数设置方法。”，其参数、调用或验证步骤直接接入Matmul 的 madType 配置、HF32/MxMatmul 模式及最终 Tiling 字段。
- [SetSingleRange](set_single_range.md)（`related`）：《SetSingleRange》处理“设置singleCoreM/singleCoreN/singleCoreK的最大值与最小值。”。《Matmul Tiling类》明确“提供Matmul矩阵乘的Host侧Tiling类，包含TCubeTiling结构体、GetTiling及形状、类型、切分等参数设置方法。”，可直接用于核对Matmul Tiling 单范围/shape/split 参数写入、查询和最终 GetTiling 产出合同。
- [GetBaseM](get_base_m.md)（`same_topic`）：GetBaseM 与《Matmul Tiling类》的实质衔接是：baseM 与 baseN/baseK 一起写入 TCubeTiling，由输入 shape、single shape 与 GetTiling 计算；Matmul 使用说明解释该块大小如何驱动 kernel 循环。
- [GetCoreNum](get_core_num.md)（`same_topic`）：总页说明 GetCoreNum 是 tiling 求解结果而非简单平台核数。
- [GetSingleShape](get_single_shape.md)（`same_topic`）：GetSingleShape 与《Matmul Tiling类》的实质衔接是：GetSingleShape 返回 GetTiling 计算出的单核 M/N/K，必须与 SetSingleShape/Range、baseM/N/K、coreNum 和 TCubeTiling 字段保持一致。
- [Matmul Tiling类使用说明](matmul_tiling_usage.md)（`same_topic`）：使用页串起类型/shape/切分设置和 GetTiling。
- [Matmul Tiling类构造函数](matmul_tiling_constructor.md)（`same_topic`）：构造是配置 tiling 对象的起点。
- [SetBufferSpace](set_buffer_space.md)（`same_topic`）：《Matmul Tiling类》明确“提供Matmul矩阵乘的Host侧Tiling类，包含TCubeTiling结构体、GetTiling及形状、类型、切分等参数设置方法。”；它与《SetBufferSpace》的“设置Matmul计算时可用的L1 Buffer/L0C Buffer/Unified Buffer/BiasTable Buffer空间大小，单位为字节。”在实际调用参数、数据流或结果校验上直接衔接。
- [SetScaleAType](set_scale_a_type.md)（`same_topic`）：《SetScaleAType》处理“MxMatmul场景，设置scaleA矩阵的位置、数据格式、是否转置等信息，这些信息需要和Kernel侧的设置保持一致。如果不调用本接口，scaleA矩阵的信息将与SetAType中设置的A矩阵的信息保持一致。”。《Matmul Tiling类》提供“提供Matmul矩阵乘的Host侧Tiling类，包含TCubeTiling结构体、GetTiling及形状、类型、切分等参数设置方法。”，其具体合同或探针直接接入MxMatmul 的 scaleA 位置/格式、Kernel scale 张量、搬运和 Mx 模式启用合同。
<!-- cannbot:related:end -->
