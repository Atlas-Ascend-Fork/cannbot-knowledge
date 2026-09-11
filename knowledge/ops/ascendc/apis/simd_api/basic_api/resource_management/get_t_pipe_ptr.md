---
type: API
title: GetTPipePtr
description: 获取创建TPipe对象时设置的全局唯一TPipe指针，获取后可进行TPipe相关的操作如InitBuffer。
tags:
- task.lookup
- topic.implementation.api_layer.basic_api
- topic.implementation.memory_management
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/resource_management/GetTPipePtr.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- '950'
- a2
- a3
- 310p
- '910'
- kirin_x90
- kirin_9030
source_headers:
- include/basic_api/kernel_common.h
---

# GetTPipePtr<a name="ZH-CN_TOPIC_0000001808018758"></a>

## 功能说明<a name="section618mcpsimp"></a>

头文件路径为：`"basic_api/kernel_common.h"`。

创建[TPipe](t_pipe/index.md)对象时，对象初始化会设置全局唯一的TPipe指针。本接口用于获取该指针，获取该指针后，可进行[TPipe](t_pipe/index.md)相关的操作。

## 函数原型<a name="section620mcpsimp"></a>

```cpp
__aicore__ inline AscendC::TPipe* GetTPipePtr()
```

## 约束说明<a name="section633mcpsimp"></a>

无

## 调用示例<a name="section6191129670"></a>

如下样例中，在核函数（Kernel）入口处创建TPipe对象，对象初始化会设置全局唯一的TPipe指针。在调用KernelAdd类Init函数时，无需显式传入TPipe指针，而是在函数内直接使用GetTPipePtr获取全局TPipe指针，用来做InitBuffer等操作。如需运行，请参考[GetTPipePtr样例](https://gitcode.com/cann/asc-devkit/tree/885973fe9fd42a600e3551af9bc11a279e6f183b/examples/01_simd_cpp_api/03_basic_api/07_tpipe_tque/get_tpipe_ptr)实现完整的代码。

```cpp
// inQueueX、inQueueY为VECIN上的TQue，outQueueZ为VECOUT上的TQue
// 获取全局TPipe指针，使用TPipe的InitBuffer接口给TQue分配内存
GetTPipePtr()->InitBuffer(inQueueX, 2, this->tileLength * sizeof(float));
GetTPipePtr()->InitBuffer(inQueueY, 2, this->tileLength * sizeof(float));
GetTPipePtr()->InitBuffer(outQueueZ, 2, this->tileLength * sizeof(float));
```


<!-- cannbot:related:start -->
## 相关

- [GetTPipePtr 错加 AscendC 命名空间导致编译失败](../../../../runbooks/compilation/gettpipeptr_is_global_function.md)（`exemplifies`）：“`GetTPipePtr` 的函数标识符声明在全局命名空间，只有返回类型是 `AscendC::TPipe*`，因此给函数名添加 `AscendC::` 会在该命名空间内查找一个不存在的成员。”给出编译失败的命名空间根因；“创建TPipe对象时，对象初始化会设置全局唯一的TPipe指针。”提供对应 API 的全局指针合同。
- [DequantBias A2/A3 ACLNN 算子知识](../../../../operators/aclnn/nn/quant/dequant_bias.md)（`related`）：“event_t eventMTE2V = static_cast<event_t>(GetTPipePtr()->FetchEventID(HardEvent::MTE2_V));”显示 DequantBias 通过全局 TPipe 指针取事件；“本接口用于获取该指针，获取该指针后，可进行TPipe相关的操作。”说明 GetTPipePtr 的返回用途。

<!-- cannbot:api-operator:start -->
### 源码中使用此 API 的算子（部分算子）

展示 10 / 216 个已匹配算子；每个 API 最多展示 10 个自动关联。
范围为算子卡声明的固定版本源码文件中的直接调用，不代表所有编译分支均执行，也不保证覆盖间接调用。

- [UpsampleBicubic2dAAGrad A2/A3 ACLNN 算子知识](../../../../operators/aclnn/cv/image/upsample_bicubic_2d_aa_grad.md)（`related`）：算子声明的固定版本源码包含对 `GetTPipePtr(...)` 的直接调用（第 563 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-cv/bb717d075d129fd1fc7b96b2886824a1d153ed2f/image/upsample_bicubic2d_aa_grad/op_kernel/upsample_bicubic2d_aa_grad.h#L563)
- [Cat 950 ACLNN 算子知识](../../../../operators/aclnn/math/conversion/cat_950.md)（`related`）：算子声明的固定版本源码包含对 `GetTPipePtr(...)` 的直接调用（第 355 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/conversion/concat/op_kernel/arch35/one_axis_concat_no_align_diff_shape.h#L355)
- [ClippedSwiglu 950 ACLNN 算子知识](../../../../operators/aclnn/nn/activation/clipped_swiglu_950.md)（`related`）：算子声明的固定版本源码包含对 `GetTPipePtr(...)` 的直接调用（第 175 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/activation/clipped_swiglu/op_kernel/arch35/clipped_swiglu_kernel.h#L175)
- [FlashAttentionScore 950 ACLNN 算子知识](../../../../operators/aclnn/transformer/attention/flash_attention_score_950.md)（`related`）：算子声明的固定版本源码包含对 `GetTPipePtr(...)` 的直接调用（第 359 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/attention/common/op_kernel/arch35/flash_attention_noquant_block_vec_base.h#L359)
- [UpsampleBilinear2dAABackward A2/A3 ACLNN 算子知识](../../../../operators/aclnn/cv/image/upsample_bilinear_2d_aa_backward.md)（`related`）：算子声明的固定版本源码包含对 `GetTPipePtr(...)` 的直接调用（第 409 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-cv/bb717d075d129fd1fc7b96b2886824a1d153ed2f/image/upsample_bilinear2d_aa_backward/op_kernel/upsample_bilinear2d_aa_backward.h#L409)
- [CircularPad2d A2/A3 ACLNN 算子知识](../../../../operators/aclnn/math/conversion/circular_pad_2d.md)（`related`）：算子声明的固定版本源码包含对 `GetTPipePtr(...)` 的直接调用（第 103 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/conversion/circular_pad/op_kernel/circular_pad_common.h#L103)
- [GeGluBackward 950 ACLNN 算子知识](../../../../operators/aclnn/nn/activation/ge_glu_backward_950.md)（`related`）：算子声明的固定版本源码包含对 `GetTPipePtr(...)` 的直接调用（第 423 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/activation/ge_glu_grad_v2/op_kernel/arch35/ge_glu_grad_v2_erf_base.h#L423)
- [FlashAttentionVarLenScore 950 ACLNN 算子知识](../../../../operators/aclnn/transformer/attention/flash_attention_var_len_score_950.md)（`related`）：算子声明的固定版本源码包含对 `GetTPipePtr(...)` 的直接调用（第 323 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/attention/common/op_kernel/arch35/flash_attention_score_block_vec_base.h#L323)
- [CircularPad2dBackward A2/A3 ACLNN 算子知识](../../../../operators/aclnn/math/conversion/circular_pad_2d_backward.md)（`related`）：算子声明的固定版本源码包含对 `GetTPipePtr(...)` 的直接调用（第 103 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/conversion/circular_pad/op_kernel/circular_pad_common.h#L103)
- [GeluQuant 950 ACLNN 算子知识](../../../../operators/aclnn/nn/activation/gelu_quant_950.md)（`related`）：算子声明的固定版本源码包含对 `GetTPipePtr(...)` 的直接调用（第 167 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/activation/gelu_quant/op_kernel/arch35/gelu_dynamic_quant_workspace_regbase.h#L167)

<!-- cannbot:api-operator:end -->
<!-- cannbot:related:end -->
