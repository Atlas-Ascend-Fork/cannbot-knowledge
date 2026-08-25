---
type: Guide
title: Cube矩阵计算编程
description: 本文介绍基于Ascend C语言扩展API，依托L1 Buffer、L0系列片上缓存实现矩阵计算的开发方法，该方式是Ascend C中最基础、通用的矩阵编程方案。AI
  Core中的Cube单元部署在AIC核，负责矩阵计算，拥有专属片上缓存：L0A Buffer存放左矩阵、L0B Buffer存放右矩阵、L0C Buffer用于保存初始累加值与矩阵运算结果。
tags: [task.lookup, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/programming_guide/programming_model/ai_core_simd_programming/c_pointer_programming/cube_matrix_computation.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# Cube矩阵计算编程

本文介绍基于Ascend C语言扩展API，依托L1 Buffer、L0系列片上缓存实现矩阵计算的开发方法，该方式是Ascend C中最基础、通用的矩阵编程方案。AI Core中的Cube单元部署在AIC核，负责矩阵计算，拥有专属片上缓存：L0A Buffer存放左矩阵、L0B Buffer存放右矩阵、L0C Buffer用于保存初始累加值与矩阵运算结果。
## Cube矩阵计算核心步骤
Cube矩阵计算整体分为数据搬入、数据加载、矩阵计算、数据搬出四个阶段，完整流程如下：
1. 通过DMA将数据从Global Memory搬运至L1 Buffer；
2. 将L1 Buffer中的数据加载至L0A Buffer、L0B Buffer；
3. 执行矩阵计算，结果存入L0C Buffer；
4. 通过DMA将计算结果从L0C Buffer搬运回Global Memory。
## 矩阵计算内存管理
### 矩阵计算内存申请
矩阵计算主要依托L0 Buffer完成运算。开发者需要先将输入数据从Global Memory搬运至L1 Buffer，再加载到L0 Buffer，最后调用Cube计算指令完成运算。L1 Buffer与L0 Buffer均通过数组形式声明，本指南主要介绍静态内存申请方式。
- 静态申请：分配一段指定大小的内存空间，空间大小在编译时确定，不可动态修改。
### 矩阵计算内存布局
Cube单元采用分块计算逻辑，硬件最小计算粒度为分形块，可并行处理多个分形。分形块大小取决于数据类型：对于half类型，分形形状为16×16（32B/sizeof(half)=16）；对于int8类型，分形形状为16×32或32×16（32B/sizeof(int8)=32）。传统行主序、列主序等线性存储模式下，读取分形块时会产生大量非连续内存访问，大幅降低访存效率。
为解决该问题，昇腾引入矩阵分形存储格式。软件层会对数据重新排布，让每个分形块在物理内存中连续存储，硬件单次读取即可加载整块数据，消除零散寻址带来的开销，有效提升数据吞吐能力。
分形粒度是Cube单元的基础计算规范，NPU架构版本2201、NPU架构版本3510全系列产品均遵循该规范，但具体分形形状因数据类型而异。昇腾Cube单元为极致发挥算力，采用不同于通用CPU的存储规则，输入、输出数据都需要匹配指定分形格式。使用Ascend C的Mmad接口开发算子时，掌握各类分形格式，是保证数据搬运、分块逻辑正确以及性能优化的关键。
为便于理解与记忆，文档采用“大Y小x”的直观命名法：
- 大Y（Z/N）：表示分形矩阵之间的排列顺序（Z为行主序，N为列主序）。
- 小x（z/n）：表示分形矩阵内部元素的排列顺序（z为行主序，n为列主序）。
### 关键分形格式详解
矩阵分形格式用于定义多维张量在内存中的排布规则。受硬件读取逻辑影响，不同产品型号对矩阵乘法 C = A × B 的格式要求存在差异：
- 针对NPU架构版本2201，矩阵乘法C = A × B要求：左矩阵A使用Zz格式，右矩阵B使用Zn格式，结果矩阵C使用Nz格式。
