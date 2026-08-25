---
type: API
title: GetTiling
description: 获取Tiling参数。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/cube_compute/Matmul_Tiling/GetTiling.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T03:58:17Z'
platforms: ['950', a2, a3]
---


# GetTiling

获取Tiling参数。

参数：
- tiling（输出）：Tiling结构体存储最终的tiling结果。TCubeTiling结构介绍请参考表1。/optiling::TCubeTiling：带有optiling命名空间的TCubeTiling结构体，，该结构体为Host侧定义的Matmul TilingData。

返回值：如果返回值不为-1，则代表Tiling计算成功，用户可以使用该Tiling结构的值。如果返回值为-1，则代表Tiling计算失败，该Tiling结果无法使用。

<!-- cannbot:related:start -->
## 相关

- [使用高阶API时配套的Tiling实现](../../../../../guides/programming_guide/advanced_programming/aclnn_operator_development/design_and_implementation/tiling_with_advanced_api.md)（`explains`）：指南在 Host TilingFunc 配置完 Matmul 形状与类型后调用 GetTiling，并以返回 -1 判失败；目标接口给出这一收口调用与返回契约。
- [BatchMatmulGetTmpBufSizeV2](../get_matmul_compute_space/batch_matmul_get_tmp_buf_size_v2.md)（`related`）：BatchMatmulGetTmpBufSizeV2 的输入必须先由 Tiling 对象 GetTiling 成功生成，返回 -1 的 tiling 不能用于空间查询。
- [EnableBias](enable_bias.md)（`related`）：Bias 开关和类型配置由 GetTiling 汇总，生成 Kernel 消费的最终参数。
- [EnableL1BankConflictOptimise](enable_l1_bank_conflict_optimise.md)（`related`）：EnableL1BankConflictOptimise 与《GetTiling》的实质衔接是：该开关由 Matmul GetTiling 判定，随后写入 MatmulConfig 并通过新增 TilingKey 选择核侧分支；bank 规则和 key 位编码共同约束实现。
- [GetBaseK](get_base_k.md)（`related`）：GetTiling 求解完成后 BaseK 才是最终硬件可用切分值。
- [GetBaseN](get_base_n.md)（`related`）：GetBaseN 只有在 GetTiling 成功计算并产出 TCubeTiling 后才有效；GetTiling 返回 -1 时 baseN 不能用于 Kernel 分块。
- [GetCoreNum](get_core_num.md)（`related`）：GetTiling 完成后才能读取最终 coreNum。
- [Init](../matmul_kernel/init.md)（`related`）：Host GetTiling 生成的 TCubeTiling 需要传给 Matmul Kernel Init，形成 Host 计算分块到 Device 初始化的接口链。
- [Matmul Tiling类使用说明](matmul_tiling_usage.md)（`related`）：Matmul Tiling 用法在设置 A/B/C 的 Position、Format、DType 后调用 GetTiling；返回非 -1 才得到可供 Kernel 使用的切分结果。
- [MatmulGetTmpBufSizeV2](../get_matmul_compute_space/matmul_get_tmp_buf_size_v2.md)（`related`）：MatmulGetTmpBufSizeV2 的输入必须是 Matmul Tiling 类 GetTiling 成功生成的 TCubeTiling，二者是 Host Tiling 到空间预算的直接调用链。
- [MultiCoreMatmulGetTmpBufSize](../get_matmul_compute_space/multi_core_matmul_get_tmp_buf_size.md)（`related`）：MultiCoreMatmulGetTmpBufSize 明确要求先由 GetTiling 生成 TCubeTiling，再据此计算各层 Buffer 使用量。
- [SetBufferSpace](set_buffer_space.md)（`related`）：《GetTiling》明确“获取Tiling参数。”；它与《SetBufferSpace》的“设置Matmul计算时可用的L1 Buffer/L0C Buffer/Unified Buffer/BiasTable Buffer空间大小，单位为字节。”在实际调用参数、数据流或结果校验上直接衔接。
- [SetDequantType](set_dequant_type.md)（`related`）：《GetTiling》明确“获取Tiling参数。”；它与《SetDequantType》的“设置Matmul量化或反量化模式，支持同一系数和向量两种量化反量化模式”在实际调用参数、数据流或结果校验上直接衔接。
- [SetDim](set_dim.md)（`related`）：《SetDim》的任务是“设置多核Matmul参与运算的核数，区分纯Cube模式和MIX模式的分离与耦合场景”。《GetTiling》具体提供“获取Tiling参数。”，它直接用于Matmul 核数、单核形状、split range 与最终 TCubeTiling 的一致性。
- [SetFixSplit](set_fix_split.md)（`related`）：《GetTiling》明确“获取Tiling参数。”；它与《SetFixSplit》的“设置固定的baseM、baseN、baseK，单位为元素个数。”在实际调用参数、数据流或结果校验上直接衔接。
- [SetMadType](set_mad_type.md)（`related`）：《SetMadType》处理“设置是否开启HF32模式。当前版本暂不支持。 对于Ascend 950PR/Ascend 950DT，本接口可用于设置是否开启HF32模式（当前版本暂不支持）、设置是否开启MxMatmul场景。在MxMatmul场景，必须调用该接口并配置为开启MxMatmul场景，从而保证该场景下正确计算并返回Tiling参数。”。《GetTiling》明确提供“获取Tiling参数。”，其参数、调用或验证步骤直接接入Matmul 的 madType 配置、HF32/MxMatmul 模式及最终 Tiling 字段。
- [SetShape](set_shape.md)（`related`）：SetShape 只写入 Tiling 输入，最终由 GetTiling 读取这些 M/N/K 配置并产出 TCubeTiling；二者构成设置到求解的调用链。
- [SetSingleRange](set_single_range.md)（`related`）：《SetSingleRange》处理“设置singleCoreM/singleCoreN/singleCoreK的最大值与最小值。”。《GetTiling》明确“获取Tiling参数。”，可直接用于核对Matmul Tiling 单范围/shape/split 参数写入、查询和最终 GetTiling 产出合同。
- [SetSparse](set_sparse.md)（`related`）：SetSparse 只写入稀疏配置，最终由 GetTiling 消费配置并求解 TCubeTiling；这是设置到求解的直接工作流。
- [SetTraverse](set_traverse.md)（`related`）：SetTraverse 只写入 FIRSTM/FIRSTN 遍历方向，最终由 GetTiling 消费该配置并产出 TCubeTiling。
- [GetBaseM](get_base_m.md)（`same_topic`）：GetBaseM 与《GetTiling》的实质衔接是：baseM 与 baseN/baseK 一起写入 TCubeTiling，由输入 shape、single shape 与 GetTiling 计算；Matmul 使用说明解释该块大小如何驱动 kernel 循环。
- [GetSingleShape](get_single_shape.md)（`same_topic`）：GetSingleShape 与《GetTiling》的实质衔接是：GetSingleShape 返回 GetTiling 计算出的单核 M/N/K，必须与 SetSingleShape/Range、baseM/N/K、coreNum 和 TCubeTiling 字段保持一致。
- [SetScaleAType](set_scale_a_type.md)（`same_topic`）：《SetScaleAType》处理“MxMatmul场景，设置scaleA矩阵的位置、数据格式、是否转置等信息，这些信息需要和Kernel侧的设置保持一致。如果不调用本接口，scaleA矩阵的信息将与SetAType中设置的A矩阵的信息保持一致。”。《GetTiling》提供“获取Tiling参数。”，其具体合同或探针直接接入MxMatmul 的 scaleA 位置/格式、Kernel scale 张量、搬运和 Mx 模式启用合同。
- [TCubeTiling结构体](t_cube_tiling_struct.md)（`same_topic`）：TCubeTiling结构体 与《GetTiling》的实质衔接是：TCubeTiling 由 GetTiling 生成、由 kernel 与空间查询消费；所选指南和越界卡解释字段配置与硬件 tile 上限。
<!-- cannbot:related:end -->
