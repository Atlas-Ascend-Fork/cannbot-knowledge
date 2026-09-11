---
type: API
title: Compare
description: 逐元素比较两个RegTensor大小，根据比较模式将结果写入MaskReg对应比特位，支持EQ/GT/LT/GE/NE/LE模式。
tags:
- task.lookup
- topic.implementation.api_layer.basic_api
- topic.compute.elementwise.comparison_logic
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/compare_and_select/Compare.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- '950'
source_headers:
- include/basic_api/reg_compute/kernel_reg_compute_vec_cmpsel_intf.h
---

# Compare<a name="ZH-CN_TOPIC_0000001929827672"></a>

## 功能说明<a name="section618mcpsimp"></a>

头文件路径为：`"basic_api/reg_compute/kernel_reg_compute_vec_cmpsel_intf.h"`。

逐元素比较两个[RegTensor](../register_data_types/reg_tensor.md)大小，根据模板参数指定的比较模式，将比较结果写入目的操作数[MaskReg](../register_data_types/mask_reg.md)中对应比特位，如果比较后的结果为真，则输出结果的对应比特位为1，否则为0。

其中cmp由模板参数mode指定比较模式，取值为EQ/GT/LT/GE/NE/LE。

## 函数原型<a name="section620mcpsimp"></a>

```cpp
template <typename T = DefaultType, CMPMODE mode = CMPMODE::EQ, typename U>
__simd_callee__ inline void Compare(MaskReg& dst, U& srcReg0, U& srcReg1, MaskReg& mask)
```

## 参数说明<a name="section622mcpsimp"></a>

**表1**  模板参数说明

| 参数名 | 描述 |
| :----- | :--- |
| T | 操作数数据类型。 |
| mode | 比较模式。支持如下取值：<br>• LT：小于<br>• GT：大于<br>• GE：大于或等于<br>• EQ：等于<br>• NE：不等于<br>• LE：小于或等于 |
| U | 源操作数的`RegTensor`类型，例如`RegTensor<half>`，由编译器自动推导，用户不需要填写。 |

**表2**  参数说明

| 参数名 | 输入/输出 | 描述 |
| :----- | :-------- | :--- |
| dst | 输出 | [MaskReg](../register_data_types/mask_reg.md)类型，目的操作数。 |
| srcReg0、srcReg1 | 输入 | 源操作数。<br>类型为[RegTensor](../register_data_types/reg_tensor.md)。<br>两个源操作数的数据类型需要与目的操作数保持一致。 |
| mask | 输入 | 源操作数元素操作的有效指示，详细说明请参考[MaskReg](../register_data_types/mask_reg.md)。 |

## 返回值说明<a name="section640mcpsimp"></a>

无

## 数据类型

**表3**  数据类型组合

| srcReg0和srcReg1数据类型 | dst数据类型 |
| :----------------------- | :---------- |
| int8_t | MaskReg |
| uint8_t | MaskReg |
| int16_t | MaskReg |
| uint16_t | MaskReg |
| half | MaskReg |
| bfloat16_t | MaskReg |
| int32_t | MaskReg |
| uint32_t | MaskReg |
| float | MaskReg |
| int64_t | MaskReg |
| uint64_t | MaskReg |

## 约束说明<a name="section633mcpsimp"></a>

- 通过mask参数控制的未选中元素在目的操作数中被置零。
- 操作数重叠约束：srcReg0和srcReg1可以是同一个`RegTensor`。

## 调用示例<a name="section642mcpsimp"></a>

```cpp
// 示例：逐元素比较src0Addr和src1Addr的数据（EQ模式），再按比较结果掩码选取元素写入dstAddr
// 输入：src0Addr指向源操作数0（如half类型[1.0, 4.0, 3.0, 2.0, 5.0, 6.0, 7.0, 8.0, 1.0, 2.0, 9.0, 3.0, 4.0, 6.0, 5.0, 7.0, ...]）
//       src1Addr指向源操作数1（如half类型[1.0, 3.0, 3.0, 5.0, 2.0, 6.0, 9.0, 4.0, 2.0, 5.0, 9.0, 1.0, 8.0, 3.0, 5.0, 6.0, ...]）
//       对应位置关系：pos0等于(1.0==1.0)、pos1大于(4.0>3.0)、pos2等于(3.0==3.0)、pos3小于(2.0<5.0)...
// 输出：dstMask为比较结果掩码（EQ模式下[1, 0, 1, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, ...]，等于位置为1，其余为0）
//       dstAddr存储按掩码Select选取的结果
template<typename T>
__simd_vf__ inline void CompareVF(__ubuf__ T* dstAddr, __ubuf__ T* src0Addr, __ubuf__ T* src1Addr, uint32_t count, uint32_t oneRepeatSize, uint16_t repeatTimes)
{
    AscendC::Reg::RegTensor<T> srcReg0;   // 源操作数0
    AscendC::Reg::RegTensor<T> srcReg1;   // 源操作数1
    AscendC::Reg::RegTensor<T> dstReg;    // 目的操作数，存储Select选取的结果
    AscendC::Reg::MaskReg mask;
    AscendC::Reg::MaskReg dstMask;        // 比较结果掩码，相等位置为1
    for (uint16_t i = 0; i < repeatTimes; i++) {
        mask = AscendC::Reg::UpdateMask<T>(count);  // 根据实际元素个数更新mask
        AscendC::Reg::LoadAlign(srcReg0, src0Addr + i * oneRepeatSize);  // 加载源操作数0
        AscendC::Reg::LoadAlign(srcReg1, src1Addr + i * oneRepeatSize);  // 加载源操作数1
        AscendC::Reg::Compare<T, AscendC::CMPMODE::EQ>(dstMask, srcReg0, srcReg1, mask);  // 逐元素比较是否相等，结果写入dstMask
        AscendC::Reg::Select(dstReg, srcReg0, srcReg1, dstMask);  // 按比较结果掩码选取元素
        AscendC::Reg::StoreAlign(dstAddr + i * oneRepeatSize, dstReg, mask);  // 将选取结果存回dstAddr
    }
}
```


<!-- cannbot:related:start -->
## 相关

<!-- cannbot:api-operator:start -->
### 源码中使用此 API 的算子（部分算子）

展示 10 / 34 个已匹配算子；每个 API 最多展示 10 个自动关联。
范围为算子卡声明的固定版本源码文件中的直接调用，不代表所有编译分支均执行，也不保证覆盖间接调用。

- [ReflectionPad2dBackward 950 ACLNN 算子知识](../../../../../operators/aclnn/math/conversion/reflection_pad_2d_backward_950.md)（`related`）：算子声明的固定版本源码包含对 `Compare(...)` 的直接调用（第 1433 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/conversion/pad_v3_grad/op_kernel/arch35/pad_v3_grad_mirror_gather.h#L1433)
- [SwigluGroupQuant 950 ACLNN 算子知识](../../../../../operators/aclnn/nn/activation/swiglu_group_quant_950.md)（`related`）：算子声明的固定版本源码包含对 `Compare(...)` 的直接调用（第 317 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/activation/swiglu_group_quant/op_kernel/arch35/swiglu_group_quant_base.h#L317)
- [QuantLightningIndexer 950 ACLNN 算子知识](../../../../../operators/aclnn/transformer/attention/quant_lightning_indexer_950.md)（`related`）：算子声明的固定版本源码包含对 `Compare(...)` 的直接调用（第 84 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/attention/lightning_indexer/op_kernel/arch35/vf/common/lightning_indexer_vector1_base.h#L84)
- [MaxDim 950 ACLNN 算子知识](../../../../../operators/aclnn/math/math/max_dim_950.md)（`related`）：算子声明的固定版本源码包含对 `Compare(...)` 的直接调用（第 234 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/math/arg_max_with_value/op_kernel/arch35/arg_max_with_value_base.h#L234)
- [Embedding 950 ACLNN 算子知识](../../../../../operators/aclnn/nn/index/embedding_950.md)（`related`）：算子声明的固定版本源码包含对 `Compare(...)` 的直接调用（第 459 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/index/gather_v2/op_kernel/arch35/gather_v2_ga_all_load.h#L459)
- [grouped_matmul_swiglu_quant 950 ACLNN 算子知识](../../../../../operators/aclnn/transformer/gmm/grouped_matmul_swiglu_quant_950.md)（`related`）：算子声明的固定版本源码包含对 `Compare(...)` 的直接调用（第 363 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/gmm/common/cgmct/epilogue/block_epilogue_swiglu_mx_quant.h#L363)
- [MinDim 950 ACLNN 算子知识](../../../../../operators/aclnn/math/math/min_dim_950.md)（`related`）：算子声明的固定版本源码包含对 `Compare(...)` 的直接调用（第 234 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/math/arg_max_with_value/op_kernel/arch35/arg_max_with_value_base.h#L234)
- [EmbeddingBag 950 ACLNN 算子知识](../../../../../operators/aclnn/nn/index/embedding_bag_950.md)（`related`）：算子声明的固定版本源码包含对 `Compare(...)` 的直接调用（第 521 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/index/embedding_bag/op_kernel/arch35/embedding_bag_regbase_common.h#L521)
- [MoeDistributeDispatchSetup 950 ACLNN 算子知识](../../../../../operators/aclnn/transformer/mc2/moe_distribute_dispatch_setup_950.md)（`related`）：算子声明的固定版本源码包含对 `Compare(...)` 的直接调用（第 104 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/mc2/moe_distribute_dispatch_v2/op_kernel/quantize_functions.h#L104)
- [Xlog1py 950 ACLNN 算子知识](../../../../../operators/aclnn/math/math/xlog1py_950.md)（`related`）：算子声明的固定版本源码包含对 `Compare(...)` 的直接调用（第 317 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/math/xlog1py/op_kernel/arch35/xlog1py_kernel.h#L317)

<!-- cannbot:api-operator:end -->
<!-- cannbot:related:end -->
