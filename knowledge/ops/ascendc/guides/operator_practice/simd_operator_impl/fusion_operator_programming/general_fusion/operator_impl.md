---
type: Guide
title: 通用融合算子实现
description: 在通算融合类算子的实现中，通信操作使用Hccl高阶API，矩阵乘计算操作使用Matmul高阶API。关于更多集合通信的内容和相关概念请参考《HCCL集合通信库》。通算融合算子的开发过程与一般算子相同，但请注意，当前通算融合算子暂不支持Kernel直调和入图（GE图）开发，仅支持单算子API调用。
tags: [task.lookup, topic.programming_model.execution_model.simd]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/operator_practice/simd_operator_impl/fusion_operator_programming/general_fusion/operator_impl.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [a2]
---

# 算子实现

在通算融合类算子的实现中，通信操作使用Hccl高阶API，矩阵乘计算操作使用Matmul高阶API。关于更多集合通信的内容和相关概念请参考《HCCL集合通信库》。通算融合算子的开发过程与一般算子相同，但请注意，当前通算融合算子暂不支持Kernel直调和入图（GE图）开发，仅支持单算子API调用。
下文将以AllGatherMatmulCustom算子（简称AllGatherMatmul）的实现为例，从算子分析、数据流分析、创建算子工程、原型定义、Tiling实现、Kernel实现、编译与运行等方面介绍通算融合算子的设计和实现流程。本样例中算子的完整代码请参见AllGatherMatmul样例。该样例仅支持在Atlas A2 训练系列产品/Atlas A2 推理系列产品上运行。
## 算子分析
算子分析是指明确算子的数学表达式、输入、输出，核函数的名称等信息。
1.  明确算子的数学表达式及通信计算逻辑。
AllGatherMatmul算子实现了AllGather通信和Matmul矩阵乘法的融合。算子逻辑为：对输入的通信矩阵a做AllGather通信得到Matmul计算的左矩阵，即通信结果gather_out，将gather_out和右矩阵b做Matmul运算得到输出c。对应的数学表达式为：
2.  明确输入、输出和属性。
-   a、b为源操作数，a为通信的输入矩阵，形状为[M, K]；b为Matmul的右矩阵，形状为[K, N]。在样例中，M、K、N分别固定为512、5120、640。
-   gather_out为目的操作数，存放AllGather通信结果，形状为[M * rankDim, K]，其中，rankDim为通信域内的卡数，在样例中固定为8。
-   c为目的操作数，存放Matmul运算结果，形状为[M * rankDim, N]。
-   算子输入输出的数据类型为float16，format为：ND。
-   group为算子属性，表示通信域名称，明确算子运行时所在的通信域。
3.  确定核函数名称和参数。
-   本样例中核函数命名为all_gather_matmul_custom。
-   根据对算子输入输出的分析，确定核函数的参数aGM，bGM，cGM，gatherOutGM；aGM，bGM为输入在Global Memory上的内存地址，cGM，gatherOutGM为输出在Global Memory上的内存地址。注意，核函数的参数和单算子API调用的输入输出在命名上存在区别，原因是核函数的参数是输入输出在Global Memory上的内存地址，而单算子API调用时输入输出的类型是aclTensor，两者并不完全一致。
4.  确定算子实现所需接口。
-   算子涉及AllGather通信，查看Ascend C  API参考中的通信相关接口，需要使用Hccl高阶API来实现AllGather通信。
-   算子涉及Matmul左右矩阵在外部存储和内部存储间的数据搬运，查看Ascend C  API参考中的数据搬运接口，需要使用DataCopy来实现数据搬运。
