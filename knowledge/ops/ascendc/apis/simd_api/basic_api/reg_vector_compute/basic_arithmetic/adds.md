---
type: API
title: Adds
description: 对srcReg按元素与标量求和，结果写入dstReg。
tags:
- task.lookup
- topic.implementation.api_layer.basic_api
- topic.programming_model.execution_unit.vector
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/basic_arithmetic/Adds.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- '950'
source_headers:
- include/basic_api/reg_compute/kernel_reg_compute_vec_binary_scalar_intf.h
---

# Adds<a name="ZH-CN_TOPIC_0000001929668280"></a>

## 功能说明<a name="section618mcpsimp"></a>

头文件路径：`"basic_api/reg_compute/kernel_reg_compute_vec_binary_scalar_intf.h"`。

该接口根据mask，对源操作数srcReg按元素与标量scalarValue进行求和操作，将结果写入目的操作数dstReg。计算公式如下：

$$
dstReg_i = srcReg_i + scalarValue
$$

## 函数原型<a name="section620mcpsimp"></a>

```cpp
template <typename T = DefaultType, typename U, MaskMergeMode mode = MaskMergeMode::ZEROING, typename S>
__simd_callee__ inline void Adds(S& dstReg, S& srcReg, U scalarValue, MaskReg& mask)
```

## 参数说明<a name="section622mcpsimp"></a>

**表 1**  模板参数说明

| 参数名 | 描述 |
| --- | --- |
| T | 矢量目的操作数和源操作数的数据类型。支持的数据类型请参考[数据类型](#数据类型)。 |
| U | 标量源操作数的数据类型。支持的数据类型请参考[数据类型](#数据类型)。 |
| mode | [MaskMergeMode](../aux_data_types/mask_merge_mode.md)枚举类型，选择MERGING模式或ZEROING模式。<br>&bull; ZEROING模式下，mask未筛选的元素在dstReg中置零。<br>&bull; MERGING模式当前不支持。 |
| S | 目的操作数的RegTensor类型，例如RegTensor&lt;half&gt;，由编译器自动推导，用户不需要填写。 |

**表 2**  参数说明

| 参数名 | 输入/输出 | 描述 |
| --- | --- | --- |
| dstReg | 输出 | 目的操作数。<br>类型为[RegTensor](../register_data_types/reg_tensor.md)。 |
| srcReg | 输入 | 源操作数。<br>类型为[RegTensor](../register_data_types/reg_tensor.md)。 |
| scalarValue | 输入 | 源操作数。<br>类型为标量。 |
| mask | 输入 | 源操作数元素操作的有效指示，详细说明请参考[MaskReg](../register_data_types/mask_reg.md)。 |

## 数据类型

目的操作数与源操作数的数据类型需要保持一致。支持的数据类型为：int8_t、uint8_t、int16_t、uint16_t、half、bfloat16_t、int32_t、uint32_t、float、complex32、int64_t、uint64_t、complex64。


## 返回值说明<a name="section640mcpsimp"></a>

无

## 约束说明<a name="section633mcpsimp"></a>

无

## 调用示例<a name="section642mcpsimp"></a>

```cpp
template<typename T>
__simd_vf__ inline void AddsVF(__ubuf__ T* dstAddr, __ubuf__ T* srcAddr, T scalarValue, uint32_t count, uint16_t oneRepeatSize, uint16_t repeatTimes)
{
    AscendC::Reg::RegTensor<T> srcReg;
    AscendC::Reg::RegTensor<T> dstReg;
    AscendC::Reg::MaskReg mask;    
    for (uint16_t i = 0; i < repeatTimes; i++) {
        mask = AscendC::Reg::UpdateMask<T>(count);
        AscendC::Reg::LoadAlign(srcReg, srcAddr + i * oneRepeatSize);
        AscendC::Reg::Adds(dstReg, srcReg, scalarValue, mask);
        AscendC::Reg::StoreAlign(dstAddr + i * oneRepeatSize, dstReg, mask);
    }
}
```



<!-- cannbot:related:start -->
## 相关

- [Adds](../../memory_vector_compute/basic_arithmetic/adds.md)（`same_topic`）：对srcReg按元素与标量求和，结果写入dstReg；计算公式 dst_i = src_i + scalarValue。两卡实现相同逐元素加标量语义；焦点是 950 RegTensor/VF 形态，候选是 LocalTensor 内存矢量接口并覆盖 950/A2/A3。

<!-- cannbot:api-operator:start -->
### 源码中使用此 API 的算子（部分算子）

展示 10 / 63 个已匹配算子；每个 API 最多展示 10 个自动关联。
范围为算子卡声明的固定版本源码文件中的直接调用，不代表所有编译分支均执行，也不保证覆盖间接调用。

- [Cat 950 ACLNN 算子知识](../../../../../operators/aclnn/math/conversion/cat_950.md)（`related`）：算子声明的固定版本源码包含对 `Adds(...)` 的直接调用（第 330 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/conversion/concat/op_kernel/arch35/one_axis_concat_no_align_diff_shape.h#L330)
- [ClippedSwiglu 950 ACLNN 算子知识](../../../../../operators/aclnn/nn/activation/clipped_swiglu_950.md)（`related`）：算子声明的固定版本源码包含对 `Adds(...)` 的直接调用（第 402 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/activation/clipped_swiglu/op_kernel/arch35/clipped_swiglu_kernel.h#L402)
- [GroupedMatmul 950 ACLNN 算子知识](../../../../../operators/aclnn/transformer/gmm/grouped_matmul_950.md)（`related`）：算子声明的固定版本源码包含对 `Adds(...)` 的直接调用（第 884 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/gmm/grouped_matmul/op_kernel/arch35/quant_adaptive_sliding_window_templates/gqmm_mix_online_dynamic.h#L884)
- [ReflectionPad2dBackward 950 ACLNN 算子知识](../../../../../operators/aclnn/math/conversion/reflection_pad_2d_backward_950.md)（`related`）：算子声明的固定版本源码包含对 `Adds(...)` 的直接调用（第 2712 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/conversion/pad_v3_grad/op_kernel/arch35/pad_v3_grad_mirror_gather.h#L2712)
- [FastGelu 950 ACLNN 算子知识](../../../../../operators/aclnn/nn/activation/fast_gelu_950.md)（`related`）：算子声明的固定版本源码包含对 `Adds(...)` 的直接调用（第 49 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/activation/fast_gelu/op_kernel/arch35/fast_gelu_dag.h#L49)
- [grouped_matmul_swiglu_quant 950 ACLNN 算子知识](../../../../../operators/aclnn/transformer/gmm/grouped_matmul_swiglu_quant_950.md)（`related`）：算子声明的固定版本源码包含对 `Adds(...)` 的直接调用（第 209 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/gmm/common/cgmct/epilogue/block_epilogue_dequant_swiglu.h#L209)
- [ReplicationPad2d 950 ACLNN 算子知识](../../../../../operators/aclnn/math/conversion/replication_pad_2d_950.md)（`related`）：算子声明的固定版本源码包含对 `Adds(...)` 的直接调用（第 267 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/conversion/pad_v3/op_kernel/arch35/pad_edge_gather.h#L267)
- [GeluQuant 950 ACLNN 算子知识](../../../../../operators/aclnn/nn/activation/gelu_quant_950.md)（`related`）：算子声明的固定版本源码包含对 `Adds(...)` 的直接调用（第 174 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/activation/gelu_quant/op_kernel/arch35/gelu_quant_base_regbase.h#L174)
- [MhcPreBackward 950 ACLNN 算子知识](../../../../../operators/aclnn/transformer/mhc/mhc_pre_backward_950.md)（`related`）：算子声明的固定版本源码包含对 `Adds(...)` 的直接调用（第 583 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/mhc/mhc_pre_backward/op_kernel/arch35/mhc_pre_backward_kernel.h#L583)
- [ReplicationPad3d 950 ACLNN 算子知识](../../../../../operators/aclnn/math/conversion/replication_pad_3d_950.md)（`related`）：算子声明的固定版本源码包含对 `Adds(...)` 的直接调用（第 267 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/conversion/pad_v3/op_kernel/arch35/pad_edge_gather.h#L267)

<!-- cannbot:api-operator:end -->
<!-- cannbot:related:end -->
