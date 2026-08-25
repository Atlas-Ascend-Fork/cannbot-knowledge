---
type: API
title: Matmul Tiling类使用说明
description: Ascend C提供一组Matmul Tiling API，方便用户获取Matmul kernel计算时所需的Tiling参数。用户只需要传入A/B/C矩阵的Position位置、Format格式和DType数据类型等信息，调用API接口，即可获取到Init中TCubeTiling结构体中的相关参数。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/cube_compute/Matmul_Tiling/Matmul_Tiling_usage.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T03:58:17Z'
platforms: ['950', a2, a3]
---


# Matmul Tiling类使用说明

Ascend C提供一组Matmul Tiling API，方便用户获取Matmul kernel计算时所需的Tiling参数。用户只需要传入A/B/C矩阵的Position位置、Format格式和DType数据类型等信息，调用API接口，即可获取到Init中TCubeTiling结构体中的相关参数。 Matmul Tiling API分为Matmul单核Tiling接口、多核Tiling接口和BatchMatmul Tiling接口，分别用于Matmul单核计算、多核计算和BatchMatmul计算场景。获取Tiling参数的流程如下： 1. 创建一个单核Tiling对象，或多核Tiling对象，或BatchMatmul Tiling对象。

<!-- cannbot:related:start -->
## 相关

- [BatchMatmulGetTmpBufSize](../get_matmul_compute_space/batch_matmul_get_tmp_buf_size.md)（`related`）：《BatchMatmulGetTmpBufSize》处理“BatchMatmul Tiling调用GetTiling接口获取Tiling参数后，根据Tiling结构体信息获取L1 Buffer/Unified Buffer/L0C Buffer的使用大小。”。《Matmul Tiling类使用说明》明确“Ascend C提供一组Matmul Tiling API，方便用户获取Matmul kernel计算时所需的Tiling参数。用户只需要传入A/B/C矩阵的Position位置、Format格式和DType数据类型等信息，调用API接口，即可获取到Init中TCubeTiling结构体中的相关参数。”，可直接用于核对BatchMatmul 临时空间估算与 Matmul Tiling 对象、TCubeTiling 结果之间的调用合同。
- [EnableL1BankConflictOptimise](enable_l1_bank_conflict_optimise.md)（`related`）：EnableL1BankConflictOptimise 与《Matmul Tiling类使用说明》的实质衔接是：该开关由 Matmul GetTiling 判定，随后写入 MatmulConfig 并通过新增 TilingKey 选择核侧分支；bank 规则和 key 位编码共同约束实现。
- [GetTiling](get_tiling.md)（`related`）：Matmul Tiling 用法在设置 A/B/C 的 Position、Format、DType 后调用 GetTiling；返回非 -1 才得到可供 Kernel 使用的切分结果。
- [Matmul Tiling类构造函数](matmul_tiling_constructor.md)（`related`）：Matmul Tiling 构造函数创建 tiling 对象，使用说明给出对象初始化、参数设置和 GetTiling 的完整顺序，能直接补全构造后的必需调用流程。
- [SetAType](set_a_type.md)（`related`）：SetAType 与《Matmul Tiling类使用说明》的实质衔接是：SetB/SetA 类型、MatmulTiling 构造与 kernel 的 SetTensorA 共同约束矩阵位置、格式、dtype、转置在 host/kernel 两侧一致。
- [SetMadType](set_mad_type.md)（`related`）：《SetMadType》处理“设置是否开启HF32模式。当前版本暂不支持。 对于Ascend 950PR/Ascend 950DT，本接口可用于设置是否开启HF32模式（当前版本暂不支持）、设置是否开启MxMatmul场景。在MxMatmul场景，必须调用该接口并配置为开启MxMatmul场景，从而保证该场景下正确计算并返回Tiling参数。”。《Matmul Tiling类使用说明》明确提供“Ascend C提供一组Matmul Tiling API，方便用户获取Matmul kernel计算时所需的Tiling参数。用户只需要传入A/B/C矩阵的Position位置、Format格式和DType数据类型等信息，调用API接口，即可获取到Init中TCubeTiling结构体中的相关参数。”，其参数、调用或验证步骤直接接入Matmul 的 madType 配置、HF32/MxMatmul 模式及最终 Tiling 字段。
- [SetOrgShape](set_org_shape.md)（`related`）：使用说明把 SetOrgShape 放进创建 tiling 对象、设置类型/形状并调用 GetTiling 的完整流程，可直接确认调用顺序和单核/多核/Batch 场景。
- [SetSingleRange](set_single_range.md)（`related`）：《SetSingleRange》处理“设置singleCoreM/singleCoreN/singleCoreK的最大值与最小值。”。《Matmul Tiling类使用说明》明确“Ascend C提供一组Matmul Tiling API，方便用户获取Matmul kernel计算时所需的Tiling参数。用户只需要传入A/B/C矩阵的Position位置、Format格式和DType数据类型等信息，调用API接口，即可获取到Init中TCubeTiling结构体中的相关参数。”，可直接用于核对Matmul Tiling 单范围/shape/split 参数写入、查询和最终 GetTiling 产出合同。
- [TCubeTiling结构体](t_cube_tiling_struct.md)（`related`）：Host Matmul Tiling 的最终产物是 TCubeTiling，Kernel Init 消费该结构中的矩阵与分块参数。
- [GetBaseM](get_base_m.md)（`same_topic`）：GetBaseM 与《Matmul Tiling类使用说明》的实质衔接是：baseM 与 baseN/baseK 一起写入 TCubeTiling，由输入 shape、single shape 与 GetTiling 计算；Matmul 使用说明解释该块大小如何驱动 kernel 循环。
- [GetSingleShape](get_single_shape.md)（`same_topic`）：GetSingleShape 与《Matmul Tiling类使用说明》的实质衔接是：GetSingleShape 返回 GetTiling 计算出的单核 M/N/K，必须与 SetSingleShape/Range、baseM/N/K、coreNum 和 TCubeTiling 字段保持一致。
- [Matmul Tiling类](matmul_tiling.md)（`same_topic`）：使用页串起类型/shape/切分设置和 GetTiling。
- [Matmul使用说明](../matmul_kernel/matmul_usage.md)（`same_topic`）：焦点处理Matmul 高阶 API 的对象配置、迭代与取结果调用顺序；Matmul Tiling类使用说明正文界定“Ascend C提供一组Matmul Tiling API，方便用户获取Matmul kernel计算时所需的Tiling参数。用户只需要传入A/B/C矩阵的Position位置、Format格式和DType数据类型等信息，调用API接口，”。候选是用法正文明确需要的注册、Init、SetTensor、Iterate、GetTensorC、Wait/End 阶段；只保留这条执行路径。
- [SetBufferSpace](set_buffer_space.md)（`same_topic`）：《Matmul Tiling类使用说明》给出“Ascend C提供一组Matmul Tiling API，方便用户获取Matmul kernel计算时所需的Tiling参数。用户只需要传入A/B/C矩阵的Position位置、Format格式和DType数据类型等信息，调用API接口，即可获取到Init中TCubeTiling结构体中的相关参数。”；该约束/探针可直接复现、解释或前置验证《SetBufferSpace》中的“设置Matmul计算时可用的L1 Buffer/L0C Buffer/Unified Buffer/BiasTable Buffer空间大小，单位为字节。”。
- [SetScaleAType](set_scale_a_type.md)（`same_topic`）：《SetScaleAType》处理“MxMatmul场景，设置scaleA矩阵的位置、数据格式、是否转置等信息，这些信息需要和Kernel侧的设置保持一致。如果不调用本接口，scaleA矩阵的信息将与SetAType中设置的A矩阵的信息保持一致。”。《Matmul Tiling类使用说明》提供“Ascend C提供一组Matmul Tiling API，方便用户获取Matmul kernel计算时所需的Tiling参数。用户只需要传入A/B/C矩阵的Position位置、Format格式和DType数据类型等信息，调用API接口，即可获取到Init中TCubeTiling结构体中的相关参数。”，其具体合同或探针直接接入MxMatmul 的 scaleA 位置/格式、Kernel scale 张量、搬运和 Mx 模式启用合同。
<!-- cannbot:related:end -->
