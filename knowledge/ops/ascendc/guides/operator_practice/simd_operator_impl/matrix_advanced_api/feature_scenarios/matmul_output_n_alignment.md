---
type: Guide
title: 矩阵乘输出的N方向对齐
description: 矩阵乘输出的N方向对齐，即矩阵乘结果C矩阵按ND_ALIGN格式输出。在Matmul矩阵乘法中，常用的矩阵数据格式有ND、NZ，相关介绍可参考数据格式章节。ND_ALIGN是矩阵的另一种数据格式，该格式一般用于N方向非32字节对齐的矩阵乘计算中，配置结果C矩阵为ND_ALIGN格式后，将按照N方向32字节对齐的补齐规则输出C矩阵，详细内容请见ND_ALIGN。
tags: [task.lookup, topic.programming_model.execution_model.simd]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/operator_practice/simd_operator_impl/matrix_advanced_api/feature_scenarios/matmul_output_n_alignment.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 矩阵乘输出的N方向对齐

## 功能介绍
矩阵乘输出的N方向对齐，即矩阵乘结果C矩阵按ND_ALIGN格式输出。在Matmul矩阵乘法中，常用的矩阵数据格式有ND、NZ，相关介绍可参考数据格式章节。ND_ALIGN是矩阵的另一种数据格式，该格式一般用于N方向非32字节对齐的矩阵乘计算中，配置结果C矩阵为ND_ALIGN格式后，将按照N方向32字节对齐的补齐规则输出C矩阵，详细内容请见ND_ALIGN。
以M=16，K=16，N=14，A、B矩阵数据类型为half的Matmul为具体示例，说明ND_ALIGN输出功能。当配置C矩阵为ND格式并输出到Global Memory时，按照原始N方向大小非32字节对齐输出如图1所示。当配置C矩阵为ND格式时，按照N方向32字节对齐输出如图2所示，C矩阵的N方向最后两列由下一行的实际数据进行填充补齐，以实现N方向对齐到32字节并输出。当配置C矩阵为ND_ALIGN格式时，Matmul API会在C矩阵的N方向上通过添加无效数据来填充最后两列，以确保N方向对齐至32字节并输出，如图3所示。
## 使用场景
Matmul计算中N方向非32字节对齐，输出C矩阵的N方向要求32字节对齐的场景。
## 约束说明
若配置C矩阵为ND_ALIGN格式输出，则为C矩阵申请的Buffer空间为N向上32字节对齐后的空间大小。

<!-- cannbot:related:start -->
## 相关

- [Matmul特性介绍](matmul_features.md)（`same_topic`）：矩阵乘输出的N方向对齐 与《Matmul特性介绍》的实质衔接是：N 方向非对齐输出依赖 ND_ALIGN 布局和 GetTensorC 搬出；局部输出、Matmul 特性、多核对齐/非对齐切分与精度 FAQ直接约束输出形状和尾块。
- [单次矩阵乘局部输出](single_matmul_local_output.md)（`same_topic`）：单次矩阵乘局部输出 与《矩阵乘输出的N方向对齐》的实质衔接是：Partial Output 只允许 MDL 的 Iterate+GetTensorC 连续写，跳过 K 累加且禁用 Bias/IterateAll；Matmul Kernel、异步/对齐和精度材料直接约束该链。
- [含有Matmul高阶API的算子精度问题](../../../../programming_guide/appendix/faq/matmul_advanced_api_precision.md)（`same_topic`）：矩阵乘输出的N方向对齐 与《含有Matmul高阶API的算子精度问题》的实质衔接是：N 方向非对齐输出依赖 ND_ALIGN 布局和 GetTensorC 搬出；局部输出、Matmul 特性、多核对齐/非对齐切分与精度 FAQ直接约束输出形状和尾块。
- [多核对齐切分](multi_core_aligned_split.md)（`same_topic`）：多核对齐切分 与《矩阵乘输出的N方向对齐》的实质衔接是：对齐切分按可用核数设置 SetDim/NumBlocks，并与非对齐尾块、N 对齐、Channel 拆分、多核 K 切分及临时空间计算共同决定实际 Matmul 分工。
- [多核非对齐切分](multi_core_unaligned_split.md)（`same_topic`）：矩阵乘输出的N方向对齐 与《多核非对齐切分》的实质衔接是：N 方向非对齐输出依赖 ND_ALIGN 布局和 GetTensorC 搬出；局部输出、Matmul 特性、多核对齐/非对齐切分与精度 FAQ直接约束输出形状和尾块。
<!-- cannbot:related:end -->
