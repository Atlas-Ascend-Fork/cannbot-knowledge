---
type: API
title: AscMmadSparse
description: 完成稀疏矩阵乘加计算，左矩阵A为稠密矩阵、右矩阵B为稀疏矩阵，B在输入前按稠密算法完成稠密化并生成索引矩阵用于A的稠密化。
tags: [task.lookup, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/cube_compute/asc_mmad_sparse.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---
# AscMmadSparse

完成矩阵乘加操作，传入的左矩阵A为稠密矩阵，右矩阵B为稀疏矩阵。对于矩阵A，在asc_mmad_sparse计算时完成稠密化；对于矩阵B，在计算执行前的输入数据准备时自行完成稠密化（按照下文中介绍的稠密算法进行稠密化），所以输入本接口的矩阵A为稠密矩阵。稠密矩阵A需要通过asc_copy_l12l0b_sparse载入，同时加载索引矩阵，索引矩阵在矩阵B稠密化的过程中生成，再用于矩阵A的稠密化。

参数：c(输出): 目的操作数，结果矩阵C，起始地址需要1024字节对齐。；a(输入): 源操作数，左矩阵A，起始地址需要512字节对齐。；b(输入): 源操作数，右矩阵B，起始地址需要512字节对齐。；m(输入): 左矩阵Height，取值范围：m∈[0,4095]。；k(输入): 左矩阵Width、右矩阵Height，取值范围：k∈[0,4095]。；n(输入): 右矩阵Width，取值范围：n∈[0,4095]。；unit_flag(输入): unit_flag是一种Mmad指令和Fixpipe指令细粒度的并行，开启该功能后，硬件每计算完一个分形，计算结果就会被搬出，该功能不适用于L0C Buffer累加的场景。取值说明如下： 0：保留值。 2：开启unit_flag，硬件执行完指令后，不会关闭unit_flag功能。 3：开启unit_flag，硬件执行完指令后，会关闭unit_flag功能。 开启该功能时，Mmad指令的unit_flag在最后一个分形设置为3，其余分形计算设置为2即可。；c_matrix_source(输入): 配置C矩阵初始值是否来源于BiasTable Buffer（存放Bias的硬件缓存区）。取值说明如下： • true：来源于BiasTable Buffer。 • false：来源于L0C Buffer。

约束：- 原始稀疏矩阵B每4个元素中应保证最多2个非零元素，如果存在3个或更多非零元素，则仅使用前2个非零元素。
- 当m、k、n中的任意一个值为0时，该指令不会被执行。

仅 Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品 支持。
