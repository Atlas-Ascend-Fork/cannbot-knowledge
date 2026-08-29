---
type: API
title: GetTiling
description: 获取Tiling参数。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/cube_compute/Matmul_Tiling/GetTiling.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T03:58:17Z'
platforms: ['950', a2, a3]
---


# GetTiling

获取Tiling参数。

参数：
- tiling（输出）：Tiling结构体存储最终的tiling结果。TCubeTiling结构介绍请参考表1。/optiling::TCubeTiling：带有optiling命名空间的TCubeTiling结构体，，该结构体为Host侧定义的Matmul TilingData。

返回值：如果返回值不为-1，则代表Tiling计算成功，用户可以使用该Tiling结构的值。如果返回值为-1，则代表Tiling计算失败，该Tiling结果无法使用。

<!-- cannbot:related:start -->
## 相关

- [使用高阶API时配套的Tiling实现](../../../../../guides/programming_guide/advanced_programming/aclnn_operator_development/design_and_implementation/tiling_with_advanced_api.md)（`explains`）：示例使用固定shape以突出配套Tiling类的接口。支持动态shape时，应从TilingContext读取M、N、K，并在调用GetTiling前校验rank、K维相等关系以及整数转换范围。；返回值：如果返回值不为-1，则代表Tiling计算成功，用户可以使用该Tiling结构的值。如果返回值为-1，则代表Tiling计算失败，该Tiling结果无法使用。高级示例明确调用 GetTiling，接口卡补齐成功和失败返回合同，可直接实现错误分支。
- [GetBaseK](get_base_k.md)（`related`）：“约束：必须使用已创建的 MatmulApiTiling 对象调用，且需在完成 GetTiling 计算后再获取 baseK，否则返回值无效。”；“返回值：如果返回值不为-1，则代表Tiling计算成功，用户可以使用该Tiling结构的值。如果返回值为-1，则代表Tiling计算失败，该Tiling结果无法使用。”。GetTiling 成功是 GetBaseK 返回有效 baseK 的明确前置条件，调用方需先检查失败码再读取基本块。
- [Init](../matmul_kernel/init.md)（`related`）：“- tiling（输出）：Tiling结构体存储最终的tiling结果。TCubeTiling结构介绍请参考表1。/optiling::TCubeTiling：带有optiling命名空间的TCubeTiling结构体，，该结构体为Host侧定义的Matmul TilingData。”；“- cubeTiling（输入）：Matmul Tiling参数，TCubeTiling结构体定义请参见表1 TCubeTiling结构说明。 Tiling参数可以通过host侧GetTiling接口获取，并传递到kernel侧使用。”。GetTiling 的结果被 Init 直接消费以初始化 Matmul 对象资源。
- [Matmul Tiling类使用说明](matmul_tiling_usage.md)（`related`）：“返回值：如果返回值不为-1，则代表Tiling计算成功，用户可以使用该Tiling结构的值。如果返回值为-1，则代表Tiling计算失败，该Tiling结果无法使用。”；“Ascend C提供一组Matmul Tiling API，方便用户获取Matmul kernel计算时所需的Tiling参数。”。使用说明给出创建 Tiling 对象并获取参数的完整调用上下文，焦点返回码决定结果能否继续传入 kernel。
- [MatmulGetTmpBufSize](../get_matmul_compute_space/matmul_get_tmp_buf_size.md)（`related`）：“- tiling（输出）：Tiling结构体存储最终的tiling结果。TCubeTiling结构介绍请参考表1。/optiling::TCubeTiling：带有optiling命名空间的TCubeTiling结构体，，该结构体为Host侧定义的Matmul TilingData。”；“本接口用于在调用GetTiling接口获取Tiling参数后，根据Tiling结构体信息获取L1 Buffer/Unified Buffer/L0C Buffer的使用大小。”。MatmulGetTmpBufSize 明确消费 GetTiling 的结果以计算三级 Buffer 资源预算。
<!-- cannbot:related:end -->
