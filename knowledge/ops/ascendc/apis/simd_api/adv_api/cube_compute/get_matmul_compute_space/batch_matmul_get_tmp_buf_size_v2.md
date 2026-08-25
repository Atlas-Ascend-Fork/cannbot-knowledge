---
type: API
title: BatchMatmulGetTmpBufSizeV2
description: BatchMatmul Tiling调用GetTiling接口获取Tiling参数后，根据Tiling结构体信息获取L1 Buffer/Unified
  Buffer/L0C Buffer的使用大小。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/cube_compute/get_Matmul_compute_space/BatchMatmulGetTmpBufSizeV2.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T03:58:17Z'
platforms: ['950', a2, a3]
---


# BatchMatmulGetTmpBufSizeV2

BatchMatmul Tiling调用GetTiling接口获取Tiling参数后，根据Tiling结构体信息获取L1 Buffer/Unified Buffer/L0C Buffer的使用大小。

参数：
- tiling（输入）：BatchMatmul Tiling的结构体，即BatchMatmulTiling对象得到的TCubeTiling结构体。 TCubeTiling为Kernel侧定义的Matmul TilingData，与入参为带AscendC::tiling命名空间的TCubeTiling结构体的GetTiling接口配合使用。
- bufSize（输出）：根据TCubeTiling结构体信息获取L1 Buffer/Unified Buffer/L0C Buffer的使用大小。 SysTilingTempBufSize结构定义如下方代码所示。

返回值：-1表示获取失败； 0表示获取成功。

<!-- cannbot:related:start -->
## 相关

- [Batch Matmul基础功能](../../../../../guides/operator_practice/simd_operator_impl/matrix_advanced_api/feature_scenarios/batch_matmul_basics.md)（`explains`）：Batch Matmul基础功能 与《BatchMatmulGetTmpBufSizeV2》的实质衔接是：Batch Matmul 直接使用 Batch tmp 查询、IterateBatch/NBatch、batch shape/输出与 batch 数配置；workspace 和精度卡约束真实使用。
- [GetTiling](../matmul_tiling/get_tiling.md)（`related`）：BatchMatmulGetTmpBufSizeV2 的输入必须先由 Tiling 对象 GetTiling 成功生成，返回 -1 的 tiling 不能用于空间查询。
- [BatchMatmulGetTmpBufSize](batch_matmul_get_tmp_buf_size.md)（`same_topic`）：《BatchMatmulGetTmpBufSize》处理“BatchMatmul Tiling调用GetTiling接口获取Tiling参数后，根据Tiling结构体信息获取L1 Buffer/Unified Buffer/L0C Buffer的使用大小。”。《BatchMatmulGetTmpBufSizeV2》明确“BatchMatmul Tiling调用GetTiling接口获取Tiling参数后，根据Tiling结构体信息获取L1 Buffer/Unified Buffer/L0C Buffer的使用大小。”，可直接用于核对BatchMatmul 临时空间估算与 Matmul Tiling 对象、TCubeTiling 结果之间的调用合同。
<!-- cannbot:related:end -->
