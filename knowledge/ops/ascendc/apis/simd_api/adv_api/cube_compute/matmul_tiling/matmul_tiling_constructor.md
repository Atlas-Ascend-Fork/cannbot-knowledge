---
type: API
title: Matmul Tiling类构造函数
description: 用于创建一个Matmul单核Tiling对象，或者多核Tiling对象，或者BatchMatmul Tiling对象。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/cube_compute/Matmul_Tiling/Matmul_Tiling_constructor.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T03:58:17Z'
platforms: ['950', a2, a3]
---


# Matmul Tiling类构造函数

用于创建一个Matmul单核Tiling对象，或者多核Tiling对象，或者BatchMatmul Tiling对象。

参数：
- ascendcPlatform（输入）：传入硬件平台的信息，PlatformAscendC定义请参见构造及析构函数。
- platform（输入）：传入硬件版本以及AI Core中各个硬件单元提供的内存大小。PlatformInfo构造时通过构造及析构函数获取。 PlatformInfo结构定义如下代码所示，socVersion通过GetSocVersion获取并透传，各类硬件存储空间大小通过GetCoreMemSize获取并透传。

<!-- cannbot:related:start -->
## 相关

- [BatchMatmulGetTmpBufSize](../get_matmul_compute_space/batch_matmul_get_tmp_buf_size.md)（`related`）：《BatchMatmulGetTmpBufSize》处理“BatchMatmul Tiling调用GetTiling接口获取Tiling参数后，根据Tiling结构体信息获取L1 Buffer/Unified Buffer/L0C Buffer的使用大小。”。《Matmul Tiling类构造函数》明确“用于创建一个Matmul单核Tiling对象，或者多核Tiling对象，或者BatchMatmul Tiling对象。”，可直接用于核对BatchMatmul 临时空间估算与 Matmul Tiling 对象、TCubeTiling 结果之间的调用合同。
- [Matmul Tiling类使用说明](matmul_tiling_usage.md)（`related`）：Matmul Tiling 构造函数创建 tiling 对象，使用说明给出对象初始化、参数设置和 GetTiling 的完整顺序，能直接补全构造后的必需调用流程。
- [SetAType](set_a_type.md)（`related`）：SetAType 与《Matmul Tiling类构造函数》的实质衔接是：SetB/SetA 类型、MatmulTiling 构造与 kernel 的 SetTensorA 共同约束矩阵位置、格式、dtype、转置在 host/kernel 两侧一致。
- [Matmul Tiling类](matmul_tiling.md)（`same_topic`）：构造是配置 tiling 对象的起点。
<!-- cannbot:related:end -->
