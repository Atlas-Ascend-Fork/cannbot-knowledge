---
type: API
title: BatchMatmulGetTmpBufSize
description: BatchMatmul Tiling调用GetTiling接口获取Tiling参数后，根据Tiling结构体信息获取L1 Buffer/Unified
  Buffer/L0C Buffer的使用大小。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/cube_compute/get_Matmul_compute_space/BatchMatmulGetTmpBufSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# BatchMatmulGetTmpBufSize

BatchMatmul Tiling调用GetTiling接口获取Tiling参数后，根据Tiling结构体信息获取L1 Buffer/Unified Buffer/L0C Buffer的使用大小。

参数：
- tiling（输入）：BatchMatmul Tiling的结构体，即BatchMatmulTiling对象得到的TCubeTiling结构体。
- bufSize（输出）：根据TCubeTiling结构体信息获取L1 Buffer/Unified Buffer/L0C Buffer的使用大小。 SysTilingTempBufSize结构定义如下方代码所示。

返回值：-1表示获取失败； 0表示获取成功。

<!-- cannbot:related:start -->
## 相关

- [BatchMatmulGetTmpBufSizeV2](batch_matmul_get_tmp_buf_size_v2.md)（`same_topic`）：TCubeTiling为Kernel侧定义的Matmul TilingData，与入参为带AscendC::tiling命名空间的TCubeTiling结构体的GetTiling接口配合使用。；tiling（输入）：BatchMatmul Tiling的结构体，即BatchMatmulTiling对象得到的TCubeTiling结构体。；两页是同一 BatchMatmul 临时空间查询合同的 V2 与原版，V2 具体增加了命名空间限定的 tiling 配合要求。
<!-- cannbot:related:end -->
