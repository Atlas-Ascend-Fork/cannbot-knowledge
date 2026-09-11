---
type: API
title: GetVecLen
description: 获取RegTensor位宽VL（Vector Length）的大小。
tags:
- task.lookup
- topic.implementation.api_layer.basic_api
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/tool_interface/system_resources_and_variables/GetVecLen.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- '950'
source_headers:
- include/basic_api/kernel_operator_sys_var_intf.h
---

# GetVecLen

## 功能说明

头文件路径为：`"basic_api/kernel_operator_sys_var_intf.h"`。

获取[RegTensor](../../reg_vector_compute/register_data_types/reg_tensor.md)位宽VL（Vector Length）的大小。

## 函数原型

```cpp
__aicore__ inline constexpr uint32_t GetVecLen()
```

## 参数说明

无

## 返回值说明

Vector Length的大小，返回常量256，单位为Byte。

## 约束说明

无

## 调用示例

如下样例通过GetVecLen获取循环迭代次数：

```cpp
template <typename T>
__aicore__ inline void AddCustomImpl(__local_mem__ T *dst, __local_mem__ T *src0, __local_mem__ T *src1,
    uint32_t calCount)
{
    AscendC::Reg::RegTensor<T> reg0;
    AscendC::Reg::RegTensor<T> reg1;
    AscendC::Reg::RegTensor<T> reg2;
    AscendC::Reg::MaskReg mask;
    constexpr uint32_t repeatElm = AscendC::GetVecLen() / sizeof(T);
    uint16_t repeatTime = AscendC::CeilDivision(calCount, repeatElm);
    for (uint16_t i = 0; i < repeatTime; ++i) {
        mask = AscendC::Reg::UpdateMask<T>(calCount);
        AscendC::Reg::LoadAlign(reg0, src0 + i * repeatElm);
        AscendC::Reg::LoadAlign(reg1, src1 + i * repeatElm);
        AscendC::Reg::Add(reg2, reg0, reg1, mask);
        AscendC::Reg::StoreAlign(dst + i * repeatElm, reg2, mask);
    }
}
```


<!-- cannbot:related:start -->
## 相关

- [Select VSEL_CMPMASK_SPR count>64 掩码错位判别](../../../../../runbooks/precision/select_vsel_cmpmask_spr_count_64.md)（`exemplifies`）：焦点接口用于“获取RegTensor位宽VL（Vector Length）的大小。”，候选卡把它用于明确决策：“对 count 大于 GetVecLen/sizeof(T) 的场景，`VSEL_TENSOR_TENSOR_MODE` 是唯一逐 repeat 重载掩码的正确模式。”；VL 直接决定 Select 是否跨 repeat 以及应选的修复模式。
- [arch35 VSEL_CMPMASK_SPR 标量批跑 mask 污染](../../../../../runbooks/precision/arch35_vsel_cmpmask_spr_mask.md)（`exemplifies`）：焦点接口用于“获取RegTensor位宽VL（Vector Length）的大小。”，候选卡在 Compare 掩码存储路径直接计算“uint32_t offset = GetVecLen() / sizeof(T) / 8;”；该偏移公式是定位小 count 掩码 padding 与 stale 数据范围的实现证据。

<!-- cannbot:api-operator:start -->
### 源码中使用此 API 的算子（部分算子）

展示 10 / 15 个已匹配算子；每个 API 最多展示 10 个自动关联。
范围为算子卡声明的固定版本源码文件中的直接调用，不代表所有编译分支均执行，也不保证覆盖间接调用。

- [CircularPad2dBackward 950 ACLNN 算子知识](../../../../../operators/aclnn/math/conversion/circular_pad_2d_backward_950.md)（`related`）：算子声明的固定版本源码包含对 `GetVecLen(...)` 的直接调用（第 88 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/conversion/pad_v3_grad/op_kernel/arch35/pad_v3_grad_circular_huge_width.h#L88)
- [RotateQuant 950 ACLNN 算子知识](../../../../../operators/aclnn/nn/matmul/rotate_quant_950.md)（`related`）：算子声明的固定版本源码包含对 `GetVecLen(...)` 的直接调用（第 168 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/matmul/common/cmct/epilogue/block_epilogue_rotate_quant.h#L168)
- [BlockSparseAttention 950 ACLNN 算子知识](../../../../../operators/aclnn/transformer/attention/block_sparse_attention_950.md)（`related`）：算子声明的固定版本源码包含对 `GetVecLen(...)` 的直接调用（第 180 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/attention/block_sparse_attention/op_kernel/attn_infra/epilogue/block/block_epilogue_online_softmax_arch35_reg_low_prec.hpp#L180)
- [ReflectionPad2dBackward 950 ACLNN 算子知识](../../../../../operators/aclnn/math/conversion/reflection_pad_2d_backward_950.md)（`related`）：算子声明的固定版本源码包含对 `GetVecLen(...)` 的直接调用（第 106 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/conversion/pad_v3_grad/op_kernel/arch35/pad_v3_grad_mirror_huge_width.h#L106)
- [AddLayerNormQuant 950 ACLNN 算子知识](../../../../../operators/aclnn/nn/norm/add_layer_norm_quant_950.md)（`related`）：算子声明的固定版本源码包含对 `GetVecLen(...)` 的直接调用（第 53 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/norm/add_layer_norm_quant/op_kernel/arch35/add_layer_norm_quant_regbase_helper.h#L53)
- [NormRopeConcat 950 ACLNN 算子知识](../../../../../operators/aclnn/transformer/posembedding/norm_rope_concat_950.md)（`related`）：算子声明的固定版本源码包含对 `GetVecLen(...)` 的直接调用（第 136 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/posembedding/norm_rope_concat/op_kernel/norm_rope_concat.h#L136)
- [Cumsum 950 ACLNN 算子知识](../../../../../operators/aclnn/math/math/cumsum_950.md)（`related`）：算子声明的固定版本源码包含对 `GetVecLen(...)` 的直接调用（第 50 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/math/cumsum/op_kernel/arch35/cumsum_4_int.h#L50)
- [GroupNormSwishGrad 950 ACLNN 算子知识](../../../../../operators/aclnn/nn/norm/group_norm_swish_grad_950.md)（`related`）：算子声明的固定版本源码包含对 `GetVecLen(...)` 的直接调用（第 199 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/norm/group_norm_swish_grad/op_kernel/arch35/group_norm_swish_grad.h#L199)
- [Xlog1py 950 ACLNN 算子知识](../../../../../operators/aclnn/math/math/xlog1py_950.md)（`related`）：算子声明的固定版本源码包含对 `GetVecLen(...)` 的直接调用（第 98 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/math/xlog1py/op_kernel/arch35/xlog1py_kernel.h#L98)
- [LayerNorm 950 ACLNN 算子知识](../../../../../operators/aclnn/nn/norm/layer_norm_950.md)（`related`）：算子声明的固定版本源码包含对 `GetVecLen(...)` 的直接调用（第 34 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/norm/layer_norm_v4/op_kernel/arch35/layer_norm_v4_common.h#L34)

<!-- cannbot:api-operator:end -->
<!-- cannbot:related:end -->
