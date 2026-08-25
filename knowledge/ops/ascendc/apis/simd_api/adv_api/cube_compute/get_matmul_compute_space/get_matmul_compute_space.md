---
type: API
title: 获取Matmul计算所需空间
description: 提供查询Matmul计算所需临时空间大小的接口，包含MultiCoreMatmulGetTmpBufSize、BatchMatmulGetTmpBufSize及其V2变体。
tags: [task.lookup, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/cube_compute/get_Matmul_compute_space/get_Matmul_compute_space.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# 获取Matmul计算所需空间

- **MultiCoreMatmulGetTmpBufSize**

- **MultiCoreMatmulGetTmpBufSizeV2**

- **BatchMatmulGetTmpBufSize**

- **BatchMatmulGetTmpBufSizeV2**

- **MatmulGetTmpBufSize**

- **MatmulGetTmpBufSizeV2**

<!-- cannbot:related:start -->
## 相关

- [BatchMatmulGetTmpBufSize](batch_matmul_get_tmp_buf_size.md)（`related`）：《BatchMatmulGetTmpBufSize》处理“BatchMatmul Tiling调用GetTiling接口获取Tiling参数后，根据Tiling结构体信息获取L1 Buffer/Unified Buffer/L0C Buffer的使用大小。”。《获取Matmul计算所需空间》明确“提供查询Matmul计算所需临时空间大小的接口，包含MultiCoreMatmulGetTmpBufSize、BatchMatmulGetTmpBufSize及其V2变体。”，可直接用于核对BatchMatmul 临时空间估算与 Matmul Tiling 对象、TCubeTiling 结果之间的调用合同。
<!-- cannbot:related:end -->
