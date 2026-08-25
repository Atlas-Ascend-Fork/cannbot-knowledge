---
type: API
title: Mmad
description: 矩阵乘加核心计算接口，封装昇腾NPU硬件矩阵乘加能力，实现C=A*B+C，广泛用于全连接层、卷积层等算子开发。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/mmad_compute/Mmad.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# Mmad

Ascend C 矩阵乘加核心接口，实现 C=A×B+C。头文件 `basic_api/kernel_operator_mm_intf.h`。矩阵 A 位于 L0A Buffer（M×K，950 格式 Nz/a2/a3 格式 Zz），矩阵 B 位于 L0B Buffer（K×N，Zn），结果 C 位于 L0C Buffer（M×N，Nz），可选用 Bias（1×N）初始化。

两个原型：不带 bias 和带 bias。参数：dst 为 LocalTensor（L0C/CO1，1024B 对齐）；fm 为左矩阵 A（L0A/A2，512B 对齐）；filter 为右矩阵 B（L0B/B2，512B 对齐）；bias 为偏置矩阵（BT/C2，64B 对齐）；mmadParams 为 MmadParams 结构体，含 mSize/kSize/nSize 等矩阵维度参数。数据类型支持 half/int8_t/int4_t 等，具体组合因型号而异。

不传 bias 原型支持 950/a2/a3/Atlas 200I/500 A2/Atlas 推理 AI Core/Atlas 训练/Kirin X90/9030；传 bias 原型不支持 Atlas 推理 AI Core/Atlas 训练/Kirin 9030。不支持 Vector Core。

<!-- cannbot:related:start -->
## 相关

- [Cube 直调 retCode=0x26：AIV 误跑 Cube API 越界](../../../../../runbooks/compilation/cube_retcode_0x26_aiv_cube_api.md)（`exemplifies`）：《Cube 直调 retCode=0x26：AIV 误跑 Cube API 越界》说明Cube 核直调 kernel 入口 extern "C" __global__ __aicore__ 未标记核类型时 bisheng 按 MIX 模式编译，kernel 被派发到 AIV 核执行 Cube 专属 API（LoadData/Mmad/Fixpipe），AIV 核无 L0A/L0B/L0C 硬件单元，访问 AIC 内部 buffer 越界，触发 aicore exception retCode=0x26 / ErrCode=507015，plog 表现为 aivector error 而非 Cube 侧错误。判别要点：代码用 Cube API、报错却是 aivector error + fixp_error 非零 + scalar access internal buffer of AICore is out of bounds。；《Mmad》说明矩阵乘加核心计算接口，封装昇腾NPU硬件矩阵乘加能力，实现C=A*B+C，广泛用于全连接层、卷积层等算子开发。。二者在报错的判别核心是未标核类型导致AIV执行LoadData/Mmad等Cube专属指令，需从kernel type和Cube调用两端验证上存在可执行的直接衔接。
- [Cube矩阵计算编程](../../../../../guides/programming_guide/programming_model/ai_core_simd_programming/c_pointer_programming/cube_matrix_computation.md)（`explains`）：Cube矩阵计算编程 与《Mmad》的实质衔接是：Cube C 指针编程按 GM→L1→L0、Mmad、L0C→GM 四阶段执行；所选架构、分形、Fmatrix、搬运、Mmad 和 tile 边界材料分别约束每一阶段。
- [Cube矩阵计算编程](../../../../../guides/programming_guide/programming_model/ai_core_simd_programming/cpp_tensor_programming/cube_matrix_computation.md)（`explains`）：《Cube矩阵计算编程》说明本文介绍如何在Ascend C中使用C++ Tensor编程API编写基于L1 Buffer、L0A Buffer等片上存储的矩阵计算代码。；《Mmad》说明矩阵乘加核心计算接口，封装昇腾NPU硬件矩阵乘加能力，实现C=A*B+C，广泛用于全连接层、卷积层等算子开发。。二者在C++ Tensor Cube编程把GM到L1/L0搬入、分形布局、Mmad计算和L0C搬出连接为完整矩阵流水上存在可执行的直接衔接。
- [SIMD算子实现耦合模式](../../../../../guides/operator_practice/simd_operator_impl/matrix_basic_api/coupled_mode.md)（`explains`）：《SIMD算子实现耦合模式》说明>本节内容为针对耦合模式，使用基础API进行矩阵乘法的编程指导。；《Mmad》说明矩阵乘加核心计算接口，封装昇腾NPU硬件矩阵乘加能力，实现C=A*B+C，广泛用于全连接层、卷积层等算子开发。。二者在耦合Cube范式的CopyIn/Split/Compute/CopyOut直接由DataCopy、LoadData、Mmad和TQue交接实现上存在可执行的直接衔接。
- [中级性能优化](../../../../../guides/operator_practice/typical_operator_cases/simd_operator_impl/matmul_leakyrelu_fusion_operator/intermediate_optimization.md)（`explains`）：中级性能优化 与《Mmad》的实质衔接是：Matmul+LeakyRelu 中级优化的正文直接串联 LoadData/Mmad/LeakyRelu、Load/Store、PipeBarrier、SetFlag 和 UnitFlag；所选故障卡约束这条融合流水。
- [中级性能优化](../../../../../guides/operator_practice/typical_operator_cases/simd_operator_impl/matmul_matrix_operator/intermediate_optimization.md)（`explains`）：中级性能优化 与《Mmad》的实质衔接是：Matmul 中级优化直接使用 GM/L1/L0 搬入、LoadData、Mmad 和 UnitFlag，前后阶段及 UnitFlag 指南支撑同一流水。
- [AscEnableHif8](../../../c_api/cube_compute/asc_enable_hif8.md)（`related`）：AscEnableHif8 只在随后 Mmad 消费 L0A/L0B 的 8bit 数据时生效，Mmad 是该模式配置的直接执行端。
- [AscHf32RoundMode](../../../c_api/enum/asc_hf32_round_mode.md)（`related`）：《AscHf32RoundMode》处理“用于Mmad计算开启HF32模式时FP32到HF32的舍入模式管理策略，在调用asc_set_hf32_round_mode时使用。”。《Mmad》明确“矩阵乘加核心计算接口，封装昇腾NPU硬件矩阵乘加能力，实现C=A*B+C，广泛用于全连接层、卷积层等算子开发。”，可直接用于核对HF32 rounding/trans mode 的配置入口及其对 Mmad 执行精度的直接影响。
- [AscSetMmadDirectionM](../../../c_api/cube_compute/asc_set_mmad_direction_m.md)（`related`）：《AscSetMmadDirectionM》说明设置矩阵乘加计算（Mmad）时逐列生成结果分形，只改变L0C Buffer上分形生成顺序，不改变计算结果。适用于UnitFlag场景下与搬出顺序一致以提升性能。；《Mmad》说明矩阵乘加核心计算接口，封装昇腾NPU硬件矩阵乘加能力，实现C=A*B+C，广泛用于全连接层、卷积层等算子开发。。二者在M/N方向配置改变Mmad输入分形与行列主序，必须在AscMmad/Mmad调用和输出Channel拆分前保持一致上存在可执行的直接衔接。
- [Conv2D（废弃）](conv2_d_deprecated.md)（`related`）：Mmad说明矩阵乘加核心计算接口，封装昇腾NPU硬件矩阵乘加能力，实现C=A*B+C，广泛用于全连接层、卷积层等算子开发。
- [Cube指令理论性能汇总](../../../../appendix/cube_instruction_theoretical_perf_summary.md)（`related`）：Mmad说明矩阵乘加核心计算接口，封装昇腾NPU硬件矩阵乘加能力，实现C=A*B+C，广泛用于全连接层、卷积层等算子开发。
- [DataCopy](../cube_compute_load/data_copy_l1_to_bias_table.md)（`related`）：DataCopy 与《Mmad》的实质衔接是：L1 到 BiasTable 的 DataCopy 位于 Mmad bias 输入链，CopyL1ToBiasTable、矩阵搬入约束和 Mmad bias 配置直接决定地址与格式是否有效。
- [K方向对齐约束](../mmad_compute_key_features/k_direction_alignment_constraint.md)（`related`）：K方向对齐约束 与《Mmad》的实质衔接是：K 对齐由 Mmad 的输入格式、数据搬运与参数配置共同决定；普通、Tensor API 和稀疏 Mmad 均需按该约束选择 K 长度及转换模式。
- [Mmad](../../cube_compute_tensor_api/mmad_compute/mmad.md)（`related`）：两张卡都执行 L0A×L0B 累加到 L0C 的 Mmad，但焦点是 Tensor API，候选是另一套基础接口与参数模型。
- [MmadWithSparse](mmad_with_sparse.md)（`related`）：MmadWithSparse 在左矩阵为 4:2 结构化稀疏时替代普通 Mmad，并额外消费稀疏索引，属于输入契约驱动的直接选型。
- [Mmad辅助配置说明](../mmad_compute_aux_config/mmad_compute_aux_config.md)（`related`）：Mmad辅助配置说明 与《Mmad》的衔接是：该配置组中的列主序/行主序与 HF32 选项会被 Mmad 执行直接消费；Tensor API 的对应辅助配置提供同一矩阵乘契约下的另一套入口。
- [Gemm（废弃）](gemm_deprecated.md)（`same_topic`）：Gemm（废弃）：Gemm 已废弃，附录确认废弃状态，正文明确把 Mmad 作为矩阵乘替代路径，因此两者形成可执行迁移关系。 目标卡《Mmad》补充：矩阵乘加核心计算接口，封装昇腾NPU硬件矩阵乘加能力，实现C=A*B+C，广泛用于全连接层、卷积层等算子开发。
- [MmadBitMode](mmad_bit_mode.md)（`same_topic`）：MmadBitMode 与 Mmad 执行同一 L0A×L0B 累加到 L0C 的矩阵乘加，BitMode 版本仅把配置参数压入位域；计算对象和结果合同一致。
- [Mmad接口边界值汇总](../../../../appendix/mmad_interface_boundary_value_summary.md)（`same_topic`）：Mmad 边界值附录明确以基础 API Mmad 的数据类型与计算语义为前提；接口卡提供调用参数，附录提供特殊值输出 oracle。
- [SetMMColumnMajor/SetMMRowMajor](../mmad_compute_aux_config/set_mm_column_major_set_mm_row_major.md)（`same_topic`）：SetMMColumnMajor/SetMMRowMajor 与《Mmad》的实质衔接是：SetMMColumnMajor/RowMajor 直接控制 Mmad/MmadWithSparse 生成方向；开启 unitFlag 且 Fixpipe 做 NZ2ND/ChannelMerge 时，方向选择还必须和搬出配置、UnitFlag 调优保持一致。
- [普通矩阵计算流程（概述）](../overview/cube_compute_flow.md)（`same_topic`）：普通矩阵计算流程（概述） 与《Mmad》的实质衔接是：普通 Cube 流程按 GM→L1→L0A/L0B 搬入、Mmad、L0C 搬出组织；分形、输入约束与数据通路卡解释每一阶段的布局和边界。
- [矩阵计算（ISASI）](mmad_compute.md)（`same_topic`）：矩阵计算（ISASI）：该集合明确以 Mmad替代废弃 Gemm/Conv2D，并要求 K方向对齐；所选卡分别给标准调用、迁移来源和最关键的输入约束，未把所有特化成员全连接。 目标卡《Mmad》补充：矩阵乘加核心计算接口，封装昇腾NPU硬件矩阵乘加能力，实现C=A*B+C，广泛用于全连接层、卷积层等算子开发。
<!-- cannbot:related:end -->
