---
type: API
title: L1 Buffer、L0A Buffer/L0B Buffer内存结构介绍
description: 为提升数据访问效率和吞吐量，Buffer采用了等容量的内存模块（Bank）结构设计。内存空间被划分为多个Bank，并以Bank为单位进一步分组形成多个Bank
  Group（BG）；每个Bank Group包含若干Bank，每个Bank都是一个可独立操作的存储单元子模块。
tags: [task.lookup, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/cube_compute_load/L1_L0A_B_memory_structure_intro.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---


# L1/L0A/L0B内存结构简介

介绍Cube计算中L1 Buffer、L0A Buffer和L0B Buffer的内存结构和数据排布方式。L1 Buffer以NZ/ZN格式存储矩阵数据，L0A和L0B以Fractal格式存储，L0C以Fractal格式存储计算结果。

各Buffer的容量和访问特性因产品型号而异。理解内存结构对于正确配置LoadData参数和优化数据搬运策略至关重要。
