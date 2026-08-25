---
type: Guide
title: SIMD算子实现耦合模式
description: '>本节内容为针对耦合模式，使用基础API进行矩阵乘法的编程指导。'
tags: [task.lookup, topic.programming_model.execution_model.simd]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/operator_practice/simd_operator_impl/matrix_basic_api/coupled_mode.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 耦合模式

## 编程范式
Cube编程范式把算子的实现流程分为5个基本任务：CopyIn，Split，Compute，Aggregate，CopyOut。CopyIn负责搬入操作，Split负责数据切分操作，Compute负责矩阵指令计算操作，Aggregate负责数据汇聚操作，CopyOut负责搬出操作。
具体任务之间的交互流程和流程图如下。
1.  Stage1：CopyIn任务。
1.  使用DataCopy接口将GlobalTensor数据拷贝到LocalTensor。
2.  使用EnQue将LocalTensor放入L1 Buffer（A1/B1）的Queue中。
2.  Stage2：Split任务。
1.  使用DeQue从L1 Buffer（A1/B1）中取出LocalTensor。
2.  使用LoadData接口将LocalTensor从L1 Buffer（A1/B1）搬运到L0A/L0B Buffer（A2/B2）。
3.  使用EnQue将计算结果LocalTensor放入到L0A/L0B Buffer（A2/B2）的Queue中。
3.  Stage3：Compute任务。
1.  使用DeQue从L0A/L0B Buffer（A2/B2）中取出LocalTensor。
2.  使用Mmad接口完成矩阵计算。
3.  使用EnQue将计算结果LocalTensor放入到L0C Buffer（CO1）的Queue中。
4.  Stage4：Aggregate任务。
1.  使用DeQue从L0C Buffer（CO1）中取出LocalTensor。
2.  使用Ascend C接口拷贝结果矩阵到逻辑位置CO2。CO2的物理存储映射与产品型号相关，具体请参考逻辑位置和物理存储的映射关系。
3.  使用EnQue将计算结果LocalTensor放入到CO2对应的Queue中。
5.  Stage5：CopyOut任务。
1.  使用DeQue接口从CO2对应的Queue中取出LocalTensor。
2.  使用DataCopy接口将LocalTensor拷贝到GlobalTensor上。
## 开发流程
基于Ascend C方式实现矩阵算子的流程如下图所示。
-   算子分析：分析算子的数学表达式、输入、输出以及计算逻辑的实现，明确需要调用的Ascend C接口。
-   核函数定义：定义Ascend C算子入口函数。
-   根据矩阵编程范式实现算子类：完成核函数的内部实现，调用私有成员函数CopyIn、SplitA、SplitB、Compute、Aggregate、CopyOut完成矩阵算子的五级流水操作。
下文将以Matmul算子为例对上述步骤进行详细介绍，Matmul算子的代码框架如下。
## 算子分析
在开发算子代码之前需要分析算子的数学表达式、输入、输出以及计算逻辑的实现，明确需要调用的Ascend C接口。
1.  明确算子的数学表达式及计算逻辑。

<!-- cannbot:related:start -->
## 相关

- [DeQue](../../../../apis/simd_api/basic_api/resource_management/t_que/de_que.md)（`explains`）：《SIMD算子实现耦合模式》说明>本节内容为针对耦合模式，使用基础API进行矩阵乘法的编程指导。；《DeQue》说明将Tensor从队列中取出用于后续处理，支持non-inplace和inplace两种接口，可通过TQueBind指定源和目的位置。。二者在耦合Cube范式的CopyIn/Split/Compute/CopyOut直接由DataCopy、LoadData、Mmad和TQue交接实现上存在可执行的直接衔接。
- [EnQue](../../../../apis/simd_api/basic_api/resource_management/t_que/en_que.md)（`explains`）：《SIMD算子实现耦合模式》说明>本节内容为针对耦合模式，使用基础API进行矩阵乘法的编程指导。；《EnQue》说明将Tensor加入队列，返回是否入队成功，可通过TQueBind指定源和目的位置实现内存复用。。二者在耦合Cube范式的CopyIn/Split/Compute/CopyOut直接由DataCopy、LoadData、Mmad和TQue交接实现上存在可执行的直接衔接。
- [LoadData](../../../../apis/simd_api/basic_api/cube_compute/cube_compute_load/load_data_2_d.md)（`explains`）：《SIMD算子实现耦合模式》说明>本节内容为针对耦合模式，使用基础API进行矩阵乘法的编程指导。；《LoadData》说明完成普通矩阵计算所需的2D格式数据搬运，以512字节的数据分形为单位，支持GM到L0A/L0B Buffer及L1 Buffer到L0A/L0B Buffer通路。。二者在耦合Cube范式的CopyIn/Split/Compute/CopyOut直接由DataCopy、LoadData、Mmad和TQue交接实现上存在可执行的直接衔接。
- [Mmad](../../../../apis/simd_api/basic_api/cube_compute/mmad_compute/mmad.md)（`explains`）：《SIMD算子实现耦合模式》说明>本节内容为针对耦合模式，使用基础API进行矩阵乘法的编程指导。；《Mmad》说明矩阵乘加核心计算接口，封装昇腾NPU硬件矩阵乘加能力，实现C=A*B+C，广泛用于全连接层、卷积层等算子开发。。二者在耦合Cube范式的CopyIn/Split/Compute/CopyOut直接由DataCopy、LoadData、Mmad和TQue交接实现上存在可执行的直接衔接。
- [SIMD算子实现基础知识](../matrix_advanced_api/basics.md)（`related`）：《SIMD算子实现耦合模式》说明>本节内容为针对耦合模式，使用基础API进行矩阵乘法的编程指导。；《SIMD算子实现基础知识》说明>本节内容为使用高阶API进行矩阵乘法的编程指导。使用高阶API进行实际的矩阵编程时，需要通过API参考确认接口支持的产品型号。。二者在耦合Cube范式的CopyIn/Split/Compute/CopyOut直接由DataCopy、LoadData、Mmad和TQue交接实现上存在可执行的直接衔接。
- [算子实现](../matrix_advanced_api/operator_impl.md)（`related`）：《SIMD算子实现耦合模式》说明>本节内容为针对耦合模式，使用基础API进行矩阵乘法的编程指导。；《算子实现》说明介绍使用Matmul高阶API实现矩阵乘算子的流程，包括Host侧Tiling参数获取与Kernel侧矩阵乘操作。。二者在耦合Cube范式的CopyIn/Split/Compute/CopyOut直接由DataCopy、LoadData、Mmad和TQue交接实现上存在可执行的直接衔接。
- [融合算子编程基础知识](../fusion_operator_programming/cv_fusion/basics.md)（`related`）：《融合算子编程基础知识》处理“>学习融合算子编程之前，请确保已经掌握矩阵编程相关知识。”。《SIMD算子实现耦合模式》明确“>本节内容为针对耦合模式，使用基础API进行矩阵乘法的编程指导。”，可直接用于核对CV 融合的数据依赖、Cube/AIV 协作、耦合模式与异步处理编程范式。
- [SIMD算子实现分离模式](decoupled_mode.md)（`same_topic`）：《SIMD算子实现耦合模式》说明>本节内容为针对耦合模式，使用基础API进行矩阵乘法的编程指导。；《SIMD算子实现分离模式》说明>本节内容为针对分离模式，使用基础API进行矩阵乘法的编程指导。。二者在耦合Cube范式的CopyIn/Split/Compute/CopyOut直接由DataCopy、LoadData、Mmad和TQue交接实现上存在可执行的直接衔接。
<!-- cannbot:related:end -->
