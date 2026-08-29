---
type: API
title: Init
description: 对Matmul对象的Tiling数据进行初始化，根据Tiling参数进行资源划分。Tiling参数可变场景下可多次调用。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/cube_compute/Matmul_Kernel/Init.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T03:58:17Z'
platforms: ['950', a2, a3]
---


# Init

Init主要用于对Matmul对象中的Tiling数据进行初始化，根据Tiling参数进行资源划分，Tiling参数的具体介绍请参考Matmul Tiling侧接口。 开发者可以先通过[REGIST_MATMUL_OBJ](regist_matmul_obj.md)不传入Tiling参数对单个Matmul对象进行初始化，后续通过Init接口单独传入Tiling参数，对Matmul对象中的Tiling数据进行调整。比如，Tiling参数可变的场景下，可以通过多次调用Init来重新设置Tiling参数。 不需要变更 Tiling 时，推荐通过 REGIST_MATMUL_OBJ 传入 Tiling 参数完成初始化。

函数原型：
__aicore__ inline void Init(const TCubeTiling* __restrict cubeTiling, TPipe* tpipe = nullptr)
__aicore__ inline void Init(const __gm__ TCubeTiling* gmCubeTiling, TPipe* tpipe = nullptr)

参数：
- cubeTiling（输入）：Matmul Tiling参数，TCubeTiling结构体定义请参见表1 TCubeTiling结构说明。 Tiling参数可以通过host侧GetTiling接口获取，并传递到kernel侧使用。
- tpipe（输入）：Tpipe对象。
- gmCubeTiling（输入）：Matmul Tiling参数，该参数指向gm上的一块内存地址，其中的数据类型是TCubeTiling结构体，TCubeTiling结构体定义请参见表1 TCubeTiling结构说明。 Tiling参数可以通过host侧GetTiling接口获取，并传递到kernel侧使用。
- tpipe（输入）：Tpipe对象。

约束：
- Tiling参数传入栈地址的接口：
- Tiling参数传入GM地址的接口：
- 仅支持Matmul Tiling参数的部分常量化场景。
- 不支持CPU域调试。

适用平台：Ascend 950PR/Ascend 950DT、Atlas A2 系列、Atlas A3 系列。未列出的产品形态不在本卡已确认范围内；详细支持矩阵以固定来源的“产品支持情况”为准。

<!-- cannbot:related:start -->
## 相关

- [ClearBias](clear_bias.md)（`related`）：Init 页说明“Init主要用于对Matmul对象中的Tiling数据进行初始化，根据Tiling参数进行资源划分”；ClearBias 页明确“如果在调用［Init］(init.md)时配置了TCubeTiling结构中的isBias参数来启用Bias，调用该接口后，会清除Bias标志位，不再启用Bias。”，后者直接修改前者初始化出的 bias 状态。
- [GetMatmulApiTiling](get_matmul_api_tiling.md)（`related`）：Init 的参数合同写明“Tiling参数可以通过host侧GetTiling接口获取，并传递到kernel侧使用。”；GetMatmulApiTiling 页说明“然后调用本接口，得到常量化的Matmul Tiling参数。”，构成 Host/编译期 Tiling 生产到 Kernel Init 消费的直接链。
- [GetTiling](../matmul_tiling/get_tiling.md)（`related`）：“- tiling（输出）：Tiling结构体存储最终的tiling结果。TCubeTiling结构介绍请参考表1。/optiling::TCubeTiling：带有optiling命名空间的TCubeTiling结构体，，该结构体为Host侧定义的Matmul TilingData。”；“- cubeTiling（输入）：Matmul Tiling参数，TCubeTiling结构体定义请参见表1 TCubeTiling结构说明。 Tiling参数可以通过host侧GetTiling接口获取，并传递到kernel侧使用。”。GetTiling 的结果被 Init 直接消费以初始化 Matmul 对象资源。
- [REGIST_MATMUL_OBJ](regist_matmul_obj.md)（`related`）：Init 页说明“开发者可以先通过［REGIST_MATMUL_OBJ］(regist_matmul_obj.md)不传入Tiling参数对单个Matmul对象进行初始化，后续通过Init接口单独传入Tiling参数”；注册页说明“当代码中只有一个Matmul对象时，本接口可以不传入tiling参数，通过Init接口单独传入tiling参数。”，双方明确给出同一注册后再初始化的调用合同。
<!-- cannbot:related:end -->
