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

- [DataCopyPad（GMToL1非对齐数据搬运）](../../../../apis/simd_api/basic_api/cube_compute/cube_compute_load/data_copy_pad_gm_to_l1.md)（`explains`）：分离模式 Matmul 规格要求“DataCopy（GMToL1随路转换-ND2NZ搬运）：Global Memory到L1 Buffer数据搬运 + ND转NZ格式转换接口”；DataCopyPad 页定义“将Global Memory中的数据搬运到L1 Buffer，支持在搬运过程中对数据进行Padding（补齐）。”，后者是非对齐输入进入前者 GM→L1 阶段的具体实现选择。
- [LoadData](../../../../apis/simd_api/basic_api/cube_compute/cube_compute_load/load_data_2_d.md)（`explains`）：分离模式 Matmul 规格列出“LoadData（2D矩阵搬运）：L1 Buffer到L0 Buffer数据搬运 + NZ转ZZ/ZN格式转换接口”；LoadData 页定义“将数据从L1 Buffer搬运到L0A或L0B Buffer的2D模式搬运接口。”，两端就是矩阵输入从 L1 到 L0A/L0B 的直接调用链。
<!-- cannbot:related:end -->
