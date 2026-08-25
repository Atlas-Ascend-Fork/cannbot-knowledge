---
type: Guide
title: SIMD算子实现分离模式
description: '>本节内容为针对分离模式，使用基础API进行矩阵乘法的编程指导。'
tags: [task.lookup, topic.programming_model.execution_model.simd]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/operator_practice/simd_operator_impl/matrix_basic_api/decoupled_mode.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---
# 分离模式

针对分离模式，由于硬件架构差异，在使用基础API进行矩阵乘法算子的实现上存在差异：
- 分离模式中，Cube计算单元与Vector计算单元分离部署，每个核有自己的Scalar单元，能独立加载自己的代码段。在核函数编写时，可通过函数类型限定符__cube__标识该核函数在设备端aicore上的Cube计算单元执行。
- 分离模式中支持Fixpipe硬件加速，支持从L0C Buffer直接搬出数据到L1 Buffer/Global Memory/Unified Buffer的同时，完成量化、反量化、数据排布格式转换等功能。
遵循算子分析、核函数定义、算子类实现的开发流程，下面以Matmul算子为例，给出分离模式下Matmul算子的代码框架。
## 算子分析
Matmul算子完成形状为[m, k]的矩阵a和形状为[k, n]的矩阵b的矩阵乘，得到形状为[m, n]的矩阵c。为了方便这里取m=k=n=32。Matmul算子的输入输出、计算逻辑以及需要调用的Ascend C接口如下表所示。
Ascend C Matmul算子设计规格
项目：内容
算子类型（OpType）：Matmul
算子输入a：shape：(m, k) = (32, 32)；data type：half；format：ND
算子输入b：shape：(k, n) = (32, 32)；data type：half；format：ND
算子输出c：shape：(m, n) = (32, 32)；data type：half；format：ND
核函数名称：matmul_custom
使用的主要接口：DataCopy（GMToL1随路转换-ND2NZ搬运）：Global Memory到L1 Buffer数据搬运 + ND转NZ格式转换接口LoadData（2D矩阵搬运）：L1 Buffer到L0 Buffer数据搬运 + NZ转ZZ/ZN格式转换接口Mmad：矩阵乘计算接口Fixpipe（L0C到GM数据搬运）：L0C Buffer到Global Memory数据搬出 + NZ转ND格式转换 + 精度转换接口
## 核函数定义
根据核函数中介绍的规则进行核函数的定义。核函数名为matmul_custom，有3个参数a，b，c，其中a，b都为输入内存，c为输出内存。使用函数类型限定符__global__来标识它是一个核函数，可以被>>调用；使用函数类型限定符__cube__来标识该核函数在设备端aicore上的Cube核执行。
核函数中，算子类的Init函数，完成内存初始化相关工作，Process函数完成算子实现的核心逻辑。核函数在开始时调用AscendC::InitSocState()初始化硬件状态，结束时调用AscendC::PipeBarrier()等待所有指令完成。
## 算子类实现
在分离模式中，一个Matmul矩阵乘算子的实现分为以下四步流水。

<!-- cannbot:related:start -->
## 相关

- [SIMD算子实现耦合模式](coupled_mode.md)（`same_topic`）：《SIMD算子实现耦合模式》说明>本节内容为针对耦合模式，使用基础API进行矩阵乘法的编程指导。；《SIMD算子实现分离模式》说明>本节内容为针对分离模式，使用基础API进行矩阵乘法的编程指导。。二者在耦合Cube范式的CopyIn/Split/Compute/CopyOut直接由DataCopy、LoadData、Mmad和TQue交接实现上存在可执行的直接衔接。
- [算子实现](../matrix_advanced_api/operator_impl.md)（`same_topic`）：算子实现 与《SIMD算子实现分离模式》的实质衔接是：该指南的核心是 host tiling→kernel Matmul 对象→Set A/B→Iterate/IterateAll→End；耦合模式、异步迭代与 CUBE_ONLY 故障直接约束实现选择。
<!-- cannbot:related:end -->
