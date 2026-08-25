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

- [ClearBias](clear_bias.md)（`related`）：ClearBias 明确用于覆盖 Init 时 TCubeTiling.isBias 启用的 Bias 状态，理解 Init 的资源/tiling 初始化是判断清除动作何时生效的前置。
- [GetMatmulApiTiling](get_matmul_api_tiling.md)（`related`）：Host/编译期生成的 Matmul tiling 参数是 Init 在 Kernel 侧划分资源的直接输入，常量化路径还能减少 Scalar 开销。
- [GetTiling](../matmul_tiling/get_tiling.md)（`related`）：Host GetTiling 生成的 TCubeTiling 需要传给 Matmul Kernel Init，形成 Host 计算分块到 Device 初始化的接口链。
- [Iterate](iterate.md)（`related`）：Iterate 与《Init》的实质衔接是：Iterate 每次推进一块 baseM×baseN 并管理 L0C；Init/SetTensor 后需按同步模式配对 GetTensorC/Wait，IterateAll/NBatch/Batch 与异步指南给出替代执行契约。
- [REGIST_MATMUL_OBJ](regist_matmul_obj.md)（`related`）：Tiling 固定时应在 REGIST_MATMUL_OBJ 阶段完成初始化；只有 tiling 运行期变化时才单独反复调用 Init。
- [矩阵计算End](end.md)（`related`）：Matmul 对象先 Init 占用计算资源；切换到另一对象前 End 释放这些资源。
- [Matmul Kernel侧接口](matmul_kernel.md)（`same_topic`）：“Matmul Kernel侧接口”处理提供Matmul矩阵乘的Kernel侧接口，包含模板参数、配置类、Init、SetTensorA/B、Iterate等方法及使用说明。；“Init”明确对Matmul对象的Tiling数据进行初始化，根据Tiling参数进行资源划分。Tiling参数可变场景下可多次调用。。实质衔接：Kernel 侧总览额外给出了注册对象、Init、设置 A/B、Iterate、GetTensorC 的最小调用顺序；只连接这条正文明确的主路径。
- [Matmul使用说明](matmul_usage.md)（`same_topic`）：焦点处理Matmul 高阶 API 的对象配置、迭代与取结果调用顺序；Init正文界定“对Matmul对象的Tiling数据进行初始化，根据Tiling参数进行资源划分。Tiling参数可变场景下可多次调用”。候选是用法正文明确需要的注册、Init、SetTensor、Iterate、GetTensorC、Wait/End 阶段；只保留这条执行路径。
- [SetBias](set_bias.md)（`same_topic`）：焦点处理Matmul SetBias 的启用/禁用状态、Tiling 类型一致性与调用时机；Init正文说明“对Matmul对象的Tiling数据进行初始化，根据Tiling参数进行资源划分。Tiling参数可变场景下可多次调用”。候选决定 Bias 是否参与、Host/Kernel 类型是否一致，或界定 SetBias 必须发生在迭代前。
- [SetTensorA](set_tensor_a.md)（`same_topic`）：Init说明对Matmul对象的Tiling数据进行初始化，根据Tiling参数进行资源划分。Tiling参数可变场景下可多次调用。
<!-- cannbot:related:end -->
