---
type: API
title: 矩阵搬入辅助配置接口
description: 矩阵搬入辅助配置接口集，包含 Fill、SetFmatrix、SetLoadDataBoundary、SetLoadDataPaddingValue 等。
tags: [task.lookup, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/cube_load_aux_config/cube_load_aux_config.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 矩阵搬入辅助配置接口

矩阵计算 ISASI 搬入阶段的辅助配置接口，用于设置搬运过程中的填充、分形与边界等参数。
包含 SetFmatrix/SetFmatrixBitMode 设置分形矩阵参数，SetLoadDataBoundary/SetLoadDataPaddingValue 设置边界与填充值，SetLoadDataRepeat/SetLoadDataRepeatWithStride 设置重复搬运参数。
另提供 Fill 填充、LoadDataUnzip/LoadUnzipIndex 解压搬运、LoadImageToLocal 图像加载及 SetAippFunctions AIPP 功能配置等接口。
