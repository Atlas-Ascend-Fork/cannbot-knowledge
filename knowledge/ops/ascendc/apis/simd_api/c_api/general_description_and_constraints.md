---
type: API
title: 通用说明和约束（C API）
description: AI Core内外包含多级存储单元，各存储单元的主要用途如下：
tags: [task.lookup, topic.programming_model]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/general_description_and_constraints.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---
# 通用说明和约束（C API）

AI Core内外包含多级存储单元：Global Memory（GM，核外共享存储）、Unified Buffer（UB，矢量计算存储）、L1/L0A/L0B/L0C Buffer（矩阵计算存储）、BiasTable Buffer（偏置数据）、Fixpipe Buffer（量化参数）。通用约束：地址重叠时单次迭代内源与目的操作数须100%重叠，多次迭代间一般不支持前序目的与后序源重叠（部分双目API的half/int32_t/float类型除外）。UB和L1总容量固定但可用容量受编译选项和混合编程场景影响。高维切分计算通过repeatTime、dataBlockStride、repeatStride和mask参数控制迭代执行与数据步长。
