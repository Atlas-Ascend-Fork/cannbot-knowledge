---
type: API
title: MatmulGetTmpBufSize
description: 本接口用于在调用GetTiling接口获取Tiling参数后，根据Tiling结构体信息获取L1 Buffer/Unified Buffer/L0C
  Buffer的使用大小。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/cube_compute/get_Matmul_compute_space/MatmulGetTmpBufSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# MatmulGetTmpBufSize

本接口用于在调用GetTiling接口获取Tiling参数后，根据Tiling结构体信息获取L1 Buffer/Unified Buffer/L0C Buffer的使用大小。

参数：
- tiling（输入）：Matmul单核Tiling的结构体，即MatmulTiling对象得到的TCubeTiling结构体。
- bufSize（输出）：Tiling中L1 Buffer/Unified Buffer/L0C Buffer的使用大小。 SysTilingTempBufSize结构定义如下方代码所示。

返回值：-1表示获取失败； 0表示获取成功。

<!-- cannbot:related:start -->
## 相关

- [BatchMatmulGetTmpBufSize](batch_matmul_get_tmp_buf_size.md)（`related`）：《BatchMatmulGetTmpBufSize》处理“BatchMatmul Tiling调用GetTiling接口获取Tiling参数后，根据Tiling结构体信息获取L1 Buffer/Unified Buffer/L0C Buffer的使用大小。”。《MatmulGetTmpBufSize》明确“本接口用于在调用GetTiling接口获取Tiling参数后，根据Tiling结构体信息获取L1 Buffer/Unified Buffer/L0C Buffer的使用大小。”，可直接用于核对BatchMatmul 临时空间估算与 Matmul Tiling 对象、TCubeTiling 结果之间的调用合同。
- [GetMatmulApiTiling](../matmul_kernel/get_matmul_api_tiling.md)（`related`）：GetMatmulApiTiling 与《MatmulGetTmpBufSize》的实质衔接是：host 侧 GetMatmulApiTiling 把模板参数、MatmulConfig 与基础配置落成 tiling，随后决定 kernel Matmul 的注册、临时空间和精度/性能策略。
- [MatmulGetTmpBufSizeV2](matmul_get_tmp_buf_size_v2.md)（`same_topic`）：MatmulGetTmpBufSize 与《MatmulGetTmpBufSizeV2》的实质衔接是：Matmul 临时空间查询与 V2/batch/multicore、buffer 预算、tiling 和 workspace 注册共同决定可用空间。
- [SetLocalWorkspace](../matmul_kernel/set_local_workspace.md)（`same_topic`）：MatmulGetTmpBufSize 与《SetLocalWorkspace》的实质衔接是：Matmul 临时空间查询与 V2/batch/multicore、buffer 预算、tiling 和 workspace 注册共同决定可用空间。
<!-- cannbot:related:end -->
