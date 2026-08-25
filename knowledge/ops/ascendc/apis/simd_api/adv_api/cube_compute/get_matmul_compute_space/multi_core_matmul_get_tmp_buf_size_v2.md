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

- [多核对齐切分](../../../../../guides/operator_practice/simd_operator_impl/matrix_advanced_api/feature_scenarios/multi_core_aligned_split.md)（`explains`）：多核对齐切分 与《MultiCoreMatmulGetTmpBufSizeV2》的实质衔接是：对齐切分按可用核数设置 SetDim/NumBlocks，并与非对齐尾块、N 对齐、Channel 拆分、多核 K 切分及临时空间计算共同决定实际 Matmul 分工。
- [BatchMatmulGetTmpBufSize](batch_matmul_get_tmp_buf_size.md)（`related`）：《BatchMatmulGetTmpBufSize》处理“BatchMatmul Tiling调用GetTiling接口获取Tiling参数后，根据Tiling结构体信息获取L1 Buffer/Unified Buffer/L0C Buffer的使用大小。”。《MultiCoreMatmulGetTmpBufSizeV2》明确“多核Matmul Tiling调用GetTiling接口获取Tiling参数后，根据Tiling结构体信息获取L1 Buffer/Unified Buffer/L0C Buffer的使用大小。”，可直接用于核对BatchMatmul 临时空间估算与 Matmul Tiling 对象、TCubeTiling 结果之间的调用合同。
- [GetCoreMemSize](../../../../utils_api/platform_info/platform_ascend_c/get_core_mem_size.md)（`related`）：GetCoreMemSize 与《MultiCoreMatmulGetTmpBufSizeV2》的实质衔接是：GetCoreMemSize 为 host tiling 提供各层容量；ReserveLocalMemory 会改变可用 UB，Matmul 空间查询与 UB 预算故障直接消费该值。
- [MultiCoreMatmulGetTmpBufSize](multi_core_matmul_get_tmp_buf_size.md)（`same_topic`）：MultiCoreMatmulGetTmpBufSizeV2 与《MultiCoreMatmulGetTmpBufSize》的实质衔接是：旧版与 V2 多核 Matmul 临时空间查询处理同一 TCubeTiling 输入，差别在命名空间结构体契约。
<!-- cannbot:related:end -->
