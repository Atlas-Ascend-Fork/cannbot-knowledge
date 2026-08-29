---
type: API
title: MultiCoreMatmulGetTmpBufSizeV2
description: 多核Matmul Tiling调用GetTiling接口获取Tiling参数后，根据Tiling结构体信息获取L1 Buffer/Unified
  Buffer/L0C Buffer的使用大小。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/cube_compute/get_Matmul_compute_space/MultiCoreMatmulGetTmpBufSizeV2.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T03:58:17Z'
platforms: ['950', a2, a3]
---


# MultiCoreMatmulGetTmpBufSizeV2

多核Matmul Tiling调用GetTiling接口获取Tiling参数后，根据Tiling结构体信息获取L1 Buffer/Unified Buffer/L0C Buffer的使用大小。

参数：
- tiling（输入）：Matmul多核Tiling的结构体，即MultiCoreMatmulTiling对象得到的TCubeTiling结构体。 TCubeTiling为Kernel侧定义的Matmul TilingData，与入参为带AscendC::tiling命名空间的TCubeTiling结构体的GetTiling接口配合使用。
- bufSize（输出）：根据TCubeTiling结构体信息获取L1 Buffer/Unified Buffer/L0C Buffer的使用大小。SysTilingTempBufSize结构定义如下方代码所示。

返回值：-1表示获取失败； 0表示获取成功。

<!-- cannbot:related:start -->
## 相关

- [MultiCoreMatmulGetTmpBufSize](multi_core_matmul_get_tmp_buf_size.md)（`same_topic`）：多核Matmul Tiling调用GetTiling接口获取Tiling参数后，根据Tiling结构体信息获取L1 Buffer/Unified Buffer/L0C Buffer的使用大小。；TCubeTiling为Kernel侧定义的Matmul TilingData，与入参为带AscendC::tiling命名空间的TCubeTiling结构体的GetTiling接口配合使用。。两卡描述同一多核 Matmul 临时空间查询契约，V2 进一步限定 TCubeTiling 与带 AscendC::tiling 命名空间的 GetTiling 配对。
<!-- cannbot:related:end -->
