---
type: API
title: Matmul使用说明
description: Ascend C提供一组Matmul高阶API，方便用户快速实现Matmul矩阵乘法的运算操作。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/cube_compute/Matmul_Kernel/Matmul_usage.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# Matmul使用说明

Ascend C提供一组Matmul高阶API，方便用户快速实现Matmul矩阵乘法的运算操作。 Matmul的计算公式为：C = A * B + Bias，其示意图如下。 - A、B为源操作数，A为左矩阵，形状为[M, K]；B为右矩阵，形状为[K, N]。 - C为目的操作数，存放矩阵乘结果的矩阵，形状为[M, N]。 - Bias为矩阵乘偏置，形状为[1, N]。对A*B结果矩阵的每一行都采用该Bias进行偏置。 图1 Matmul矩阵乘示意图

涵盖以下类别：实现原理。

<!-- cannbot:related:start -->
## 相关

- [GetNormalConfig](get_normal_config.md)（`related`）：GetNormalConfig 与《Matmul使用说明》的实质衔接是：GetNormalConfig 生成 MatmulConfig 并选择 Norm/MDL/Basic 等模板参数；batchLoop 和 VecND2NZ 会直接要求 IterateNBatch、local workspace 与对应搬运路径，tiling/注册材料说明配置如何被消费。
- [Iterate](iterate.md)（`related`）：Iterate 与《Matmul使用说明》的实质衔接是：Iterate 每次推进一块 baseM×baseN 并管理 L0C；Init/SetTensor 后需按同步模式配对 GetTensorC/Wait，IterateAll/NBatch/Batch 与异步指南给出替代执行契约。
- [IterateAll](iterate_all.md)（`related`）：《IterateAll》说明调用一次IterateAll，会计算出singleCoreM \ singleCoreN大小的C矩阵。迭代顺序可通过tiling参数iterateOrder调整。；《Matmul使用说明》说明Ascend C提供一组Matmul高阶API，方便用户快速实现Matmul矩阵乘法的运算操作。。二者在IterateAll一次完成singleCoreM×singleCoreN，异步模式必须配WaitIterateAll并按GetTensorC/输出场景消费结果上存在可执行的直接衔接。
- [MatmulCallBackFunc](matmul_call_back_func.md)（`related`）：《MatmulCallBackFunc》说明模板参数，支持用户定制化Matmul的A、B、C矩阵搬入搬出功能，传入自定义回调函数指针替换默认搬运函数。；《Matmul使用说明》说明Ascend C提供一组Matmul高阶API，方便用户快速实现Matmul矩阵乘法的运算操作。。二者在回调类型由Matmul模板参数、配置与Policy实例化，并经注册宏和用户自定义信息进入Kernel侧Matmul对象上存在可执行的直接衔接。
- [MatmulPolicy](matmul_policy.md)（`related`）：Matmul 使用说明展示由模板参数实例化对象并执行计算的入口，使策略类型与实际对象声明相衔接。
- [MatmulTemplateParams](matmul_template_params.md)（`related`）：Matmul 使用说明给出 C=A*B+Bias 的操作数语义，可用于为 MatmulTemplateParams 的 A/B/C/Bias 类型参数选择正确矩阵角色。
- [REGIST_MATMUL_OBJ](regist_matmul_obj.md)（`related`）：Matmul 使用说明落实 REGIST 必须早于 InitBuffer、对象数上限和多对象 tiling 配对的调用顺序。
- [SetOrgShape](set_org_shape.md)（`related`）：“SetOrgShape”定义：设置Matmul计算原始完整的形状M、N、K，单位为元素个数。用于运行时修改shape，比如复用同一个Matmul对象，从不同的矩阵块取数据计算。；“Matmul使用说明”定义：Ascend C提供一组Matmul高阶API，方便用户快速实现Matmul矩阵乘法的运算操作。。实质衔接：Host tiling 与 Kernel 对象必须对原始 M/N/K 一致；复用对象处理矩阵块时还需区分完整 org shape 与当前 single shape。
- [SetSubBlockIdx](set_sub_block_idx.md)（`related`）：SetSubBlockIdx：SetSubBlockIdx与GetSubBlockIdx是同一 AIV 子核身份的写读契约，REGIST_MATMUL_OBJ会自动设置该值；双 AIV flag runbook说明错误 subBlock 身份如何破坏跨核同步。 目标卡《Matmul使用说明》补充：Ascend C提供一组Matmul高阶API，方便用户快速实现Matmul矩阵乘法的运算操作。
- [SetTensorB](set_tensor_b.md)（`related`）：SetTensorB 与《Matmul使用说明》的衔接是：SetTensorB 的地址范围和转置解释同时受 SetOrgShape、Tiling侧 SetBType/ISTRANS 约束；Matmul 使用流程还要求与 SetTensorA 成对准备输入。
- [SetUserDefInfo](set_user_def_info.md)（`related`）：SetUserDefInfo 与《Matmul使用说明》的实质衔接是：SetUserDefInfo 只在 MatmulCallBackFunc 使用 tilingPtr 时需要；SetSelfDefineData承载回调的可变数据，模板参数和使用说明决定回调是否启用。
- [WaitIterateAll](wait_iterate_all.md)（`related`）：WaitIterateAll 与《Matmul使用说明》的实质衔接是：WaitIterateAll 是 IterateAll 连续写 GM 异步路径的完成屏障；异步场景、Matmul 用法及 TensorC 获取协议说明何时等待以及等待后何时可消费输出。
- [DisableBias](disable_bias.md)（`same_topic`）：焦点处理Matmul 高阶 API 的对象配置、迭代与取结果调用顺序；DisableBias正文界定“清除Bias标志位，表示Matmul计算时没有Bias参与。如果在初始化时配置了TCubeTiling结构中的isBias参数来启用Bias，调用该接口后，会清除Bias标志位，不再启用Bias”。候选是用法正文明确需要的注册、Init、SetTensor、Iterate、GetTensorC、Wait/End 阶段；只保留这条执行路径。
- [GetMatmulApiTiling](get_matmul_api_tiling.md)（`same_topic`）：GetMatmulApiTiling 与《Matmul使用说明》的实质衔接是：host 侧 GetMatmulApiTiling 把模板参数、MatmulConfig 与基础配置落成 tiling，随后决定 kernel Matmul 的注册、临时空间和精度/性能策略。
- [GetOffsetC](get_offset_c.md)（`same_topic`）：GetOffsetC 与《Matmul使用说明》的实质衔接是：GetOffsetC 返回当前 Matmul 分片在完整 C 矩阵的位置；Iterate 推进分片，GetTensorC 消费结果，Kernel/使用说明给出该预留位置信息所在的执行链。
- [GetTensorC](get_tensor_c.md)（`same_topic`）：《GetTensorC》说明Iterate后获取C矩阵分片，可输出到GM或UB，支持同步与异步两种模式。；《Matmul使用说明》说明Ascend C提供一组Matmul高阶API，方便用户快速实现Matmul矩阵乘法的运算操作。。二者在Iterate产出的C分片必须按同步或异步GetTensorC协议搬出，并在异步模式等待完成后才能复用资源上存在可执行的直接衔接。
- [Init](init.md)（`same_topic`）：焦点处理Matmul 高阶 API 的对象配置、迭代与取结果调用顺序；Init正文界定“对Matmul对象的Tiling数据进行初始化，根据Tiling参数进行资源划分。Tiling参数可变场景下可多次调用”。候选是用法正文明确需要的注册、Init、SetTensor、Iterate、GetTensorC、Wait/End 阶段；只保留这条执行路径。
- [IterateNBatch](iterate_n_batch.md)（`same_topic`）：IterateNBatch 与《Matmul使用说明》的实质衔接是：IterateNBatch 必须先开启 MatmulConfig::isNBatch、配置 Host 侧 batch 信息并申请 workspace；同步/异步结果分别经 WaitIterateBatch 或 GetBatchTensorC/GetBatchC 获取，使用说明给出完整调用顺序。
- [Matmul Kernel侧接口](matmul_kernel.md)（`same_topic`）：“Matmul Kernel侧接口”处理提供Matmul矩阵乘的Kernel侧接口，包含模板参数、配置类、Init、SetTensorA/B、Iterate等方法及使用说明。；“Matmul使用说明”明确Ascend C提供一组Matmul高阶API，方便用户快速实现Matmul矩阵乘法的运算操作。。实质衔接：Kernel 侧总览额外给出了注册对象、Init、设置 A/B、Iterate、GetTensorC 的最小调用顺序；只连接这条正文明确的主路径。
- [Matmul Tiling类使用说明](../matmul_tiling/matmul_tiling_usage.md)（`same_topic`）：焦点处理Matmul 高阶 API 的对象配置、迭代与取结果调用顺序；Matmul Tiling类使用说明正文界定“Ascend C提供一组Matmul Tiling API，方便用户获取Matmul kernel计算时所需的Tiling参数。用户只需要传入A/B/C矩阵的Position位置、Format格式和DType数据类型等信息，调用API接口，”。候选是用法正文明确需要的注册、Init、SetTensor、Iterate、GetTensorC、Wait/End 阶段；只保留这条执行路径。
- [MatmulConfig](matmul_config.md)（`same_topic`）：焦点处理Matmul 高阶 API 的对象配置、迭代与取结果调用顺序；MatmulConfig正文界定“模板参数MatmulConfig，用于配置Matmul模板信息以及相关的配置参数。不配置默认开启Norm模板，Norm模板的介绍请参考表模板特性。MatmulConfig的参数说明见表2。MatmulConfig的定义方式有：”。候选是用法正文明确需要的注册、Init、SetTensor、Iterate、GetTensorC、Wait/End 阶段；只保留这条执行路径。
- [SetBias](set_bias.md)（`same_topic`）：焦点处理Matmul SetBias 的启用/禁用状态、Tiling 类型一致性与调用时机；Matmul使用说明正文说明“Ascend C提供一组Matmul高阶API，方便用户快速实现Matmul矩阵乘法的运算操作”。候选决定 Bias 是否参与、Host/Kernel 类型是否一致，或界定 SetBias 必须发生在迭代前。
- [SetLocalWorkspace](set_local_workspace.md)（`same_topic`）：焦点处理Matmul 高阶 API 的对象配置、迭代与取结果调用顺序；SetLocalWorkspace正文界定“设置Matmul内部额外占用的UB临时空间，由用户预留并申请LocalTensor后传入，需在Iterate前调用”。候选是用法正文明确需要的注册、Init、SetTensor、Iterate、GetTensorC、Wait/End 阶段；只保留这条执行路径。
- [SetTensorA](set_tensor_a.md)（`same_topic`）：焦点处理Matmul 高阶 API 的对象配置、迭代与取结果调用顺序；SetTensorA正文界定“设置矩阵乘的左矩阵A”。候选是用法正文明确需要的注册、Init、SetTensor、Iterate、GetTensorC、Wait/End 阶段；只保留这条执行路径。
- [WaitGetTensorC](wait_get_tensor_c.md)（`same_topic`）：焦点处理Matmul 高阶 API 的对象配置、迭代与取结果调用顺序；WaitGetTensorC正文界定“当使用GetTensorC异步接口将结果矩阵从GM拷贝到UB，且UB后续需要进行Vector计算时，需要调用WaitGetTensorC进行同步”。候选是用法正文明确需要的注册、Init、SetTensor、Iterate、GetTensorC、Wait/End 阶段；只保留这条执行路径。
- [矩阵计算End](end.md)（`same_topic`）：焦点处理Matmul 高阶 API 的对象配置、迭代与取结果调用顺序；矩阵计算End正文界定“多个Matmul对象之间切换计算时，必须调用一次End函数，用于释放Matmul计算资源，防止多个Matmul对象的计算资源冲突”。候选是用法正文明确需要的注册、Init、SetTensor、Iterate、GetTensorC、Wait/End 阶段；只保留这条执行路径。
<!-- cannbot:related:end -->
