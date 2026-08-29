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

- [AscSetMmadDirectionM](asc_set_mmad_direction_m.md)（`related`）：本接口是Ascend C面向昇腾AI芯片的矩阵乘加（Mmad）核心计算接口；本接口需在矩阵乘加指令（asc_mmad、asc_mmad_mx）执行前调用，以此来确保模式配置在矩阵乘加计算过程中生效。；方向 M 配置是 asc_mmad 执行前的持久前置状态，直接决定结果分形生成顺序。
- [AscSetMmadDirectionN](asc_set_mmad_direction_n.md)（`related`）：本接口是Ascend C面向昇腾AI芯片的矩阵乘加（Mmad）核心计算接口；本接口需在矩阵乘加指令（asc_mmad、asc_mmad_mx）执行前调用，以此来确保模式配置在矩阵乘加计算过程中生效。；方向 N 配置同样是 asc_mmad 的显式前置合同，并在 NZ2ND 或 Channel Merge 组合下改变生成方向。
<!-- cannbot:related:end -->
