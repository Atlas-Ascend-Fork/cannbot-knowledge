---
type: API
title: MatmulGetTmpBufSizeV2
description: 单核Matmul Tiling调用GetTiling接口获取Tiling参数后，根据Tiling结构体信息获取L1 Buffer/Unified
  Buffer/L0C Buffer的使用大小。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/cube_compute/get_Matmul_compute_space/MatmulGetTmpBufSizeV2.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T03:58:17Z'
platforms: ['950', a2, a3]
---


# MatmulGetTmpBufSizeV2

单核Matmul Tiling调用GetTiling接口获取Tiling参数后，根据Tiling结构体信息获取L1 Buffer/Unified Buffer/L0C Buffer的使用大小。

参数：
- tiling（输入）：Matmul单核Tiling的结构体，即MatmulTiling对象得到的TCubeTiling结构体。 TCubeTiling为Kernel侧定义的Matmul TilingData，与入参为带AscendC::tiling命名空间的TCubeTiling结构体的GetTiling接口配合使用。
- bufSize（输出）：根据TCubeTiling结构体信息获取L1 Buffer/Unified Buffer/L0C Buffer的使用大小。 SysTilingTempBufSize结构定义如下方代码所示。

返回值：-1表示获取失败； 0表示获取成功。

<!-- cannbot:related:start -->
## 相关

- [BatchMatmulGetTmpBufSize](batch_matmul_get_tmp_buf_size.md)（`related`）：《BatchMatmulGetTmpBufSize》处理“BatchMatmul Tiling调用GetTiling接口获取Tiling参数后，根据Tiling结构体信息获取L1 Buffer/Unified Buffer/L0C Buffer的使用大小。”。《MatmulGetTmpBufSizeV2》明确“单核Matmul Tiling调用GetTiling接口获取Tiling参数后，根据Tiling结构体信息获取L1 Buffer/Unified Buffer/L0C Buffer的使用大小。”，可直接用于核对BatchMatmul 临时空间估算与 Matmul Tiling 对象、TCubeTiling 结果之间的调用合同。
- [GetMatmulApiTiling](../matmul_kernel/get_matmul_api_tiling.md)（`related`）：GetMatmulApiTiling 与《MatmulGetTmpBufSizeV2》的实质衔接是：host 侧 GetMatmulApiTiling 把模板参数、MatmulConfig 与基础配置落成 tiling，随后决定 kernel Matmul 的注册、临时空间和精度/性能策略。
- [GetTiling](../matmul_tiling/get_tiling.md)（`related`）：MatmulGetTmpBufSizeV2 的输入必须是 Matmul Tiling 类 GetTiling 成功生成的 TCubeTiling，二者是 Host Tiling 到空间预算的直接调用链。
- [MatmulGetTmpBufSize](matmul_get_tmp_buf_size.md)（`same_topic`）：MatmulGetTmpBufSize 与《MatmulGetTmpBufSizeV2》的实质衔接是：Matmul 临时空间查询与 V2/batch/multicore、buffer 预算、tiling 和 workspace 注册共同决定可用空间。
<!-- cannbot:related:end -->
