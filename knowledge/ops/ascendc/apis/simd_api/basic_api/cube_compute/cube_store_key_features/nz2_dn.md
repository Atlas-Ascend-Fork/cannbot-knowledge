---
type: API
title: NZ2DN
description: 矩阵计算的搬出过程中NZ2DN的核心功能体现为，将NZ格式矩阵转化为DN格式矩阵。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/cube_store_key_features/NZ2DN.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# NZ2DN

矩阵搬出时将 NZ 格式矩阵转换为 DN 格式矩阵。通过 FixpipeParamsArch3510 的 config=CFG_COLUMN_MAJOR 开启。

参数：dnNum 为 DN 矩阵个数、mSize/nSize 为矩阵 M/N 方向维度、srcStride 为源 NZ 矩阵相邻 Z 排布间隔（单位 C0_Size）、dstStride 为目的 DN 矩阵每行元素个数（单位 element）、srcNzMatrixStride 为不同源 NZ 矩阵间隔（C0_Size）、dstDnMatrixStride 为相邻目的 DN 矩阵间隔（element）、srcNzC0Stride 为源 NZ 分形相邻行偏移（C0_Size）。仅 Ascend 950PR/950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [卷积格式转换](convolution_format_conversion.md)（`related`）：特别的，针对Ascend 950PR/Ascend 950DT产品，还支持Fixpipe指令通过NZ2DN能力，将L0C Buffer上数据转为NCHW格式输出。转换示意图如下所示：；矩阵搬出时将 NZ 格式矩阵转换为 DN 格式矩阵。通过 FixpipeParamsArch3510 的 config=CFG_COLUMN_MAJOR 开启。。格式转换卡指定 950 的 NZ2DN 输出 NCHW，API 卡补齐列主序开关和 DN stride 参数。
<!-- cannbot:related:end -->
