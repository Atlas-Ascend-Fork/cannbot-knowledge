---
type: Guide
title: TSCM输入的矩阵乘
description: 用户自行管理TSCM内存空间，Matmul直接使用传入的TSCM地址，不进行GM到TSCM的数据搬入。
tags: [task.lookup, topic.programming_model.execution_model.simd]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/operator_practice/simd_operator_impl/matrix_advanced_api/feature_scenarios/tscm_input_matmul.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# TSCM输入的矩阵乘

## 功能介绍
TSCM表示L1 Buffer空间对应的逻辑内存，L1 Buffer相关内容见存储单元，开发者可以自行管理TSCM以高效利用硬件资源。比如，开发者可缓存一份TSCM数据，在不同使用场景中灵活配置为Matmul操作的A矩阵、B矩阵或Bias偏置矩阵，实现内存复用与计算效率优化。在TSCM输入场景，用户管理整块TSCM内存空间，Matmul直接使用传入的TSCM内存地址，不进行Global Memory到TSCM的数据搬入。
## 使用场景
用户需要自定义数据搬入到TSCM及自定义管理的场景，即需要自定义实现数据搬入功能，如非连续搬入或对搬入数据进行预处理等。用户通过自定义管理TSCM可灵活配置MTE2流水，实现跨Matmul对象的全局DoubleBuffer，MTE2相关内容见搬运单元。
## 约束说明
设置为TSCM输入的矩阵必须在TSCM中全载，全载即全部的矩阵数据同时搬入及保持在TSCM中。
