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
