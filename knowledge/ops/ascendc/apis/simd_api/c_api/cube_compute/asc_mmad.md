---
type: API
title: AscMmad
description: Ascend C矩阵乘加（Mmad）核心计算接口，封装昇腾NPU硬件矩阵乘加能力，用于全连接层、卷积层等神经网络算子开发。
tags: [task.lookup, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/cube_compute/asc_mmad.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---
# AscMmad

本接口是Ascend C面向昇腾AI芯片的矩阵乘加（Mmad）核心计算接口，专为高性能算子开发设计，封装了昇腾NPU硬件的矩阵乘加计算能力，广泛用于神经网络层（如全连接层、卷积层）、数值计算类算子的开发。
本接口为矩阵计算接口，仅在AIC上生效。

参数：c_matrix(输出): 目的操作数，结果矩阵C在L0C Buffer中的起始地址，需按照1024字节对齐。数据类型由接口重载决定，具体请参见支持的数据类型组合。；a_matrix(输入): 源操作数，左矩阵A在L0A Buffer中的起始地址，需按照512字节对齐。数据类型由接口重载决定，具体请参见支持的数据类型组合。；b_matrix(输入): 源操作数，右矩阵B在L0B Buffer中的起始地址，需按照512字节对齐。数据类型由接口重载决定，具体请参见支持的数据类型组合。；left_height(输入): 左矩阵A和结果矩阵C的M维大小，单位为元素，取值范围为[0, 4095]。；n_dim(输入): 左矩阵A和右矩阵B的K维大小，单位为元素，取值范围为[0, 4095]。；right_width(输入): 右矩阵B和结果矩阵C的N维大小，单位为元素，取值范围为[0, 4095]。

约束：- 本接口仅在AIC上生效，在AIV上调用将直接返回。
- left_height、n_dim、right_width中的任意一个值为0时，接口将被视为NOP（空操作）。

- 内存使用约束说明
  - 针对Ascend 950PR/Ascend 950DT
      - L0C Buffer大小为256KB，L0A Buffer和L0B Buffer大小均为64KB。BiasTable Buffer大小为4KB。矩阵的起始地址和占用空间不能超出对应Buffer的范围。
      - 各矩阵的起始地址需满足参数说明中的对齐要求。操作数的其他地址约束

仅 Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品 支持。

<!-- cannbot:related:start -->
## 相关

- [Cube 直调 retCode=0x26：AIV 误跑 Cube API 越界](../../../../runbooks/compilation/cube_retcode_0x26_aiv_cube_api.md)（`exemplifies`）：《Cube 直调 retCode=0x26：AIV 误跑 Cube API 越界》说明Cube 核直调 kernel 入口 extern "C" __global__ __aicore__ 未标记核类型时 bisheng 按 MIX 模式编译，kernel 被派发到 AIV 核执行 Cube 专属 API（LoadData/Mmad/Fixpipe），AIV 核无 L0A/L0B/L0C 硬件单元，访问 AIC 内部 buffer 越界，触发 aicore exception retCode=0x26 / ErrCode=507015，plog 表现为 aivector error 而非 Cube 侧错误。判别要点：代码用 Cube API、报错却是 aivector error + fixp_error 非零 + scalar access internal buffer of AICore is out of bounds。；《AscMmad》说明Ascend C矩阵乘加（Mmad）核心计算接口，封装昇腾NPU硬件矩阵乘加能力，用于全连接层、卷积层等神经网络算子开发。。二者在报错的判别核心是未标核类型导致AIV执行LoadData/Mmad等Cube专属指令，需从kernel type和Cube调用两端验证上存在可执行的直接衔接。
- [Cube矩阵计算编程](../../../../guides/programming_guide/programming_model/ai_core_simd_programming/c_pointer_programming/cube_matrix_computation.md)（`explains`）：Cube矩阵计算编程 与《AscMmad》的实质衔接是：Cube C 指针编程按 GM→L1→L0、Mmad、L0C→GM 四阶段执行；所选架构、分形、Fmatrix、搬运、Mmad 和 tile 边界材料分别约束每一阶段。
- [中级性能优化](../../../../guides/operator_practice/typical_operator_cases/simd_operator_impl/matmul_matrix_operator/intermediate_optimization.md)（`explains`）：中级性能优化 与《AscMmad》的实质衔接是：Matmul 中级优化直接使用 GM/L1/L0 搬入、LoadData、Mmad 和 UnitFlag，前后阶段及 UnitFlag 指南支撑同一流水。
- [AscHf32RoundMode](../enum/asc_hf32_round_mode.md)（`related`）：《AscHf32RoundMode》处理“用于Mmad计算开启HF32模式时FP32到HF32的舍入模式管理策略，在调用asc_set_hf32_round_mode时使用。”。《AscMmad》明确“Ascend C矩阵乘加（Mmad）核心计算接口，封装昇腾NPU硬件矩阵乘加能力，用于全连接层、卷积层等神经网络算子开发。”，可直接用于核对HF32 rounding/trans mode 的配置入口及其对 Mmad 执行精度的直接影响。
- [AscSetFp32Mode](asc_set_fp32_mode.md)（`related`）：AscSetFp32Mode 与《AscMmad》的实质衔接是：AscSetFp32Mode 与 HF32 round/enable/trans 配置共同决定 AscMmad 的 FP32/HF32 计算模式，Mmad 约束和 HF32 指南说明精度与方向设置。
- [AscSetMmadDirectionN](asc_set_mmad_direction_n.md)（`related`）：方向配置必须在 asc_mmad 前调用，并决定其 L0C 结果分形生成顺序。
- [Cube指令理论性能汇总](../../../appendix/cube_instruction_theoretical_perf_summary.md)（`related`）：AscMmad说明Ascend C矩阵乘加（Mmad）核心计算接口，封装昇腾NPU硬件矩阵乘加能力，用于全连接层、卷积层等神经网络算子开发。
- [K方向对齐约束](../../basic_api/cube_compute/mmad_compute_key_features/k_direction_alignment_constraint.md)（`related`）：AscMmad 与《K方向对齐约束》的实质衔接是：AscMmad 在 AIC 上消费 L0A/L0B 并累加到 L0C；Mmad 约束、方向/HF32 配置、Cube 流程和 AIV 误调用故障共同覆盖实际调用边界。
- [Mmad](../../basic_api/cube_compute_tensor_api/mmad_compute/mmad.md)（`related`）：AscMmad 与《Mmad》的实质衔接是：AscMmad 在 AIC 上消费 L0A/L0B 并累加到 L0C；Mmad 约束、方向/HF32 配置、Cube 流程和 AIV 误调用故障共同覆盖实际调用边界。
- [Mmad接口边界值汇总](../../../appendix/mmad_interface_boundary_value_summary.md)（`related`）：AscMmad 与《Mmad接口边界值汇总》的实质衔接是：AscMmad 在 AIC 上消费 L0A/L0B 并累加到 L0C；Mmad 约束、方向/HF32 配置、Cube 流程和 AIV 误调用故障共同覆盖实际调用边界。
- [Mmad计算关键特性说明](../../basic_api/cube_compute/mmad_compute_key_features/mmad_compute_key_features.md)（`related`）：AscMmad 与《Mmad计算关键特性说明》的实质衔接是：AscMmad 在 AIC 上消费 L0A/L0B 并累加到 L0C；Mmad 约束、方向/HF32 配置、Cube 流程和 AIV 误调用故障共同覆盖实际调用边界。
- [Mmad辅助配置说明](../../basic_api/cube_compute/mmad_compute_aux_config/mmad_compute_aux_config.md)（`related`）：AscMmad 与《Mmad辅助配置说明》的实质衔接是：AscMmad 在 AIC 上消费 L0A/L0B 并累加到 L0C；Mmad 约束、方向/HF32 配置、Cube 流程和 AIV 误调用故障共同覆盖实际调用边界。
- [SetHF32Mode](../../basic_api/cube_compute/mmad_compute_aux_config/set_hf32_mode.md)（`related`）：AscMmad 与《SetHF32Mode》的实质衔接是：AscMmad 在 AIC 上消费 L0A/L0B 并累加到 L0C；Mmad 约束、方向/HF32 配置、Cube 流程和 AIV 误调用故障共同覆盖实际调用边界。
- [SetMMColumnMajor/SetMMRowMajor](../../basic_api/cube_compute/mmad_compute_aux_config/set_mm_column_major_set_mm_row_major.md)（`related`）：AscMmad 与《SetMMColumnMajor/SetMMRowMajor》的实质衔接是：AscMmad 在 AIC 上消费 L0A/L0B 并累加到 L0C；Mmad 约束、方向/HF32 配置、Cube 流程和 AIV 误调用故障共同覆盖实际调用边界。
- [基础APIGEMV](../../basic_api/cube_compute_tensor_api/mmad_compute_key_features/gemv.md)（`related`）：《基础APIGEMV》处理“GEMV的核心功能体现为：当矩阵A的维度M取值为1时，接口可以手动启用GEMV功能，该操作退化为1×K维度的行向量与K×N维度矩阵之间的乘法运算。”。《AscMmad》明确提供“Ascend C矩阵乘加（Mmad）核心计算接口，封装昇腾NPU硬件矩阵乘加能力，用于全连接层、卷积层等神经网络算子开发。”，其参数、调用或验证步骤直接接入GEMV 的 Mmad 形状、行主序布局、对齐、Tiling 和结果验证。
- [普通矩阵计算流程（概述）](../../basic_api/cube_compute/overview/cube_compute_flow.md)（`related`）：AscMmad 与《普通矩阵计算流程（概述）》的实质衔接是：AscMmad 在 AIC 上消费 L0A/L0B 并累加到 L0C；Mmad 约束、方向/HF32 配置、Cube 流程和 AIV 误调用故障共同覆盖实际调用边界。
- [AscSetMmadDirectionM](asc_set_mmad_direction_m.md)（`same_topic`）：AscMmad 与《AscSetMmadDirectionM》的实质衔接是：AscMmad 在 AIC 上消费 L0A/L0B 并累加到 L0C；Mmad 约束、方向/HF32 配置、Cube 流程和 AIV 误调用故障共同覆盖实际调用边界。
- [矩阵计算](cube_compute.md)（`same_topic`）：AscMmad 与《矩阵计算》的实质衔接是：AscMmad 在 AIC 上消费 L0A/L0B 并累加到 L0C；Mmad 约束、方向/HF32 配置、Cube 流程和 AIV 误调用故障共同覆盖实际调用边界。
<!-- cannbot:related:end -->
