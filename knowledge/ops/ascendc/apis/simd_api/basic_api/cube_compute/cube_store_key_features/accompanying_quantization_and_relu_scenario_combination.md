---
type: API
title: 随路量化与随路ReLU场景组合
description: 矩阵搬出支持多种随路量化与随路ReLU的组合，芯片支持的全量场景组合参考下表，接下来将对下表中的随路量化ReLU算法逐一介绍。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/cube_store_key_features/accompanying_quantization_and_relu_scenario_combination.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 随路量化与随路ReLU场景组合

矩阵搬出支持随路量化与随路 ReLU 的组合。M1 为原始数据正数时使用的系数，M2 为负数时使用的系数。NPU 架构版本 2201：M1/M2 取 QUANT_PRE[31:0]（scalar）或 Quant_PRE_ADDR[i][31:0]（tensor），i 为列索引。NPU 架构版本 3510（950）：M1/M2 取 QUANT_PRE[31:13] 或 Quant_PRE_ADDR[i][31:13]。

组合规则：no ReLU 时 M1=M2=量化参数；Normal ReLU 时 M1=量化参数、M2=0。支持的 quantPre 模式含 REQ8/DEQF16/QF322B8_PRE（scalar）及 VREQ8/VDEQF16/VQF322B8_PRE（tensor），3510 额外支持 FP8/HIF8/BF16/F32 等扩展模式。
