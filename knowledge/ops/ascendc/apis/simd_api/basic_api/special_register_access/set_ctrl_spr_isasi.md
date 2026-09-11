---
type: API
title: SetCtrlSpr
description: 对CTRL寄存器的特定比特位进行设置，通过模板参数指定比特位范围并写入对应值。
tags:
- task.lookup
- topic.implementation.api_layer.basic_api
- topic.programming_model.system_variable
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/special_register_access/SetCtrlSpr_ISASI.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- '950'
- a2
- a3
source_headers:
- include/basic_api/kernel_operator_common_intf.h
---

# SetCtrlSpr(ISASI)

## 功能说明

头文件路径为：`"basic_api/kernel_operator_common_intf.h"`。

对CTRL寄存器（控制寄存器）的特定比特位进行设置。通过模板参数startBit和endBit指定目标比特位范围，将运行参数value（超出比特位范围会出现编译报错）写入CTRL寄存器对应位置。

## 函数原型

```cpp
template <int8_t startBit, int8_t endBit>
__aicore__ static inline void SetCtrlSpr(int64_t value)
```

## 参数说明

**表1** 模板参数说明

| 参数名 | 描述 |
| --- | --- |
| startBit | 起始比特位索引。 |
| endBit | 终止比特位索引。 |

**表2** 参数说明

| 参数名 | 输入/输出 | 描述 |
| --- | --- | --- |
| value | 输入 | 起止比特位上新设置的值。 |



**表3** Ascend 950PR/Ascend 950DT常用CTRL寄存器比特位说明<a id="tab-950"></a>

| CTRL寄存器比特位 | 功能 | 默认值 | 配合使用的API |
| --- | --- | --- | --- |
| CTRL[8:6] | 用于控制数据从L0C Buffer/Unified Buffer（UB）/L1 Buffer搬运至Global Memory时原子操作的启用及数据类型选择。<br>&bull; 3'b000：不开启原子操作；<br>&bull; 3'b001：开启原子操作，数据类型为float；<br>&bull; 3'b010：开启原子操作，数据类型为half；<br>&bull; 3'b011：开启原子操作，数据类型为int16_t；<br>&bull; 3'b100：开启原子操作，数据类型为int32_t；<br>&bull; 3'b101：开启原子操作，数据类型为int8_t；<br>&bull; 3'b110：开启原子操作，数据类型为bfloat16_t。 | 3'b000 | 配合使用API：<br>&bull; 数据搬运API。 |
| CTRL[10:9] | 用于控制原子操作的类型，仅在CTRL[8:6]开启原子操作时生效。<br>&bull; 2'b00：选择ADD操作；<br>&bull; 2'b01：选择MAX操作；<br>&bull; 2'b10：选择MIN操作。 | 2'b00 | 不涉及 |
| CTRL[45] | 用于控制左右矩阵数据做Mmad计算时的处理方式。<br>&bull; 1'b0：按照原数据类型进行处理；<br>&bull; 1'b1：左右矩阵数据均为fp8_e4m3fn_t时，数据视为hifloat8_t进行矩阵乘法计算。其他场景按照原数据类型进行处理。 | 1'b0 | 不涉及 |
| CTRL[48] | 用于控制浮点数计算和浮点数精度转换时的饱和模式，仅在CTRL[60]开启时生效。<br>&bull; 1'b0：饱和模式，inf输出会被饱和为±MAX，NaN输出会被饱和为0；<br>&bull; 1'b1：非饱和模式，inf/NaN保持原输出。<br><br>该控制位仅支持如下数据类型：<br>&bull;浮点数计算时支持half数据类型；<br>&bull;浮点数精度转换时支持如下数据类型：hifloat8_t、fp8_e8m0_t、fp8_e5m2_t、fp8_e4m3fn_t、half、bfloat16_t。 | 1'b0 | 配合使用的API：<br>&bull; 矢量计算API；<br>&bull; 原子操作API；<br>&bull; 精度转换指令。<br><br>使用约束：<br>&bull; 需要满足数据类型限制。<br>&bull; 执行原子操作过程中，如果需要重新配置该控制位，需要调用[DataCacheCleanAndInvalid](../cache_control/data_cache_clean_and_invalid.md)先清除当前Cache Line状态并将当前数据写出，防止饱和模式变更影响当前数据。具体调用示例可参考[原子操作中，half类型配置全局非饱和模式示例。](#example2)。 |
| CTRL[50] | 用于控制浮点数精度转换时的NaN饱和模式，在CTRL[48]设置为饱和模式时生效。<br>&bull; 1'b0：NaN输出会被转换为0.0；<br>&bull; 1'b1：NaN输出会保持NaN。<br><br>该控制位仅支持如下数据类型：<br>fp8_e8m0_t、fp8_e5m2_t、fp8_e4m3fn_t。 | 1'b0 | 精度转换指令（需要满足数据类型限制）。 |
| CTRL[53] | 用于控制整数计算指令的饱和模式。<br>&bull; 1'b0：截断模式，溢出值按目标数据类型位数截断，保留低位，舍弃高位；<br>&bull; 1'b1：饱和模式，溢出值饱和到±MAX。 | 1'b0 | 矢量计算API（输入输出数据类型为整数）。 |
| CTRL[59] | 用于控制浮点数转整数或整数转整数时的精度转换饱和模式，仅在CTRL[60]开启时生效。<br>&bull; 1'b0：饱和模式：溢出值饱和到±MAX；<br>&bull; 1'b1：截断模式：溢出值按目标数据类型位数截断，保留低位，舍弃高位。 | 1'b0 | 精度转换指令。 |
| CTRL[60] | 用于控制饱和模式的全局生效方式。<br>&bull; 1'b0：单指令设置饱和；<br>&bull; 1'b1：全局设置饱和。 | 1'b1 | 该控制位可与Reg矢量计算API [Cast](../reg_vector_compute/type_conversion/cast.md)配合使用，或与CTRL[48]、CTRL[59]配合使用，具体配置信息参考[Ascend 950PR/Ascend 950DT饱和模式全局或单指令生效配置表](#table231122118201)。 |





**表4** Atlas A3 训练系列产品/Atlas A3 推理系列产品常用CTRL寄存器比特位说明

| CTRL寄存器比特位 | 功能 | 默认值 | 配合使用的API |
| --- | --- | --- | --- |
| CTRL[48] | 用于控制浮点数计算和浮点数精度转换时的饱和模式。<br>&bull; 1'b0：饱和模式，inf输出会被饱和为±MAX， NaN输出会被饱和为0；<br>&bull; 1'b1：非饱和模式，inf/NaN保持原输出。<br><br>该控制位仅支持如下数据类型：<br>&bull;浮点数计算时支持half、bfloat16_t数据类型；<br>&bull;浮点数精度转换时支持如下数据类型：half、bfloat16_t。 | 1'b0 | 不涉及 |

**注：针对Atlas A3 训练系列产品/Atlas A3 推理系列产品，推荐使用[SetSaturationFlag](set_saturation_flag_isasi.md)和[GetSaturationFlag](get_saturation_flag_isasi.md)来设置和获取CTRL[48]以控制饱和模式。**





**表5** Atlas A2 训练系列产品/Atlas A2 推理系列产品常用CTRL寄存器比特位说明

| CTRL寄存器比特位 | 功能 | 默认值 | 配合使用的API |
| --- | --- | --- | --- |
| CTRL[48] | 用于控制浮点数计算和浮点数精度转换时的饱和模式。<br>&bull; 1'b0：饱和模式，inf输出会被饱和为±MAX， NaN输出会被饱和为0；<br>&bull; 1'b1：非饱和模式，inf/NaN保持原输出。<br><br>该控制位仅支持如下数据类型：<br>&bull;浮点数计算时支持half、bfloat16_t数据类型；<br>&bull;浮点数精度转换时支持如下数据类型：half、bfloat16_t。 | 1'b0 | 不涉及 |

**注：针对Atlas A2 训练系列产品/Atlas A2 推理系列产品，推荐使用[SetSaturationFlag](set_saturation_flag_isasi.md)和[GetSaturationFlag](get_saturation_flag_isasi.md)来设置和获取CTRL[48]以控制饱和模式。**





**表6** Ascend 950PR/Ascend 950DT饱和模式全局或单指令生效配置表<a id="table231122118201"></a>

| 全局开启位 | 控制位 | 功能描述 |
| --- | --- | --- |
| CTRL[60] = 1'b0 | Reg矢量计算Cast API的trait模板参数中satMode设置为SatMode::NO_SAT。 | 单指令非饱和模式。 |
| CTRL[60] = 1'b0 | Reg矢量计算Cast API的trait模板参数中satMode设置为SatMode::SAT。 | 单指令饱和模式。 |
| CTRL[60] = 1'b1 | CTRL[48] = 1'b1 | 全局非饱和模式（浮点数计算和浮点数精度转换）。 |
| CTRL[60] = 1'b1 | CTRL[48] = 1'b0 | 全局饱和模式（浮点数计算和浮点数精度转换）。 |
| CTRL[60] = 1'b1 | CTRL[59] = 1'b1 | 全局非饱和模式（浮点数转整数或整数转整数时的精度转换）。 |
| CTRL[60] = 1'b1 | CTRL[59] = 1'b0 | 全局饱和模式（浮点数转整数或整数转整数时的精度转换）。 |



## 数据类型

本接口为寄存器访问接口，不涉及张量数据类型操作。参数value类型固定为int64_t。

## 返回值说明

无

## 约束说明


- Ascend 950PR/Ascend 950DT仅支持CTRL[8:6]、CTRL[10:9]、CTRL[45]、CTRL[48]、CTRL[50]、CTRL[53]、CTRL[59]、CTRL[60]比特位。


- Atlas A3 训练系列产品/Atlas A3 推理系列产品仅支持CTRL[48]比特位。


- Atlas A2 训练系列产品/Atlas A2 推理系列产品仅支持CTRL[48]比特位。


- Ascend 950PR/Ascend 950DT对于CTRL[8:6]和CTRL[10:9]的设置，已封装原子操作API，建议通过这些原子操作API进行配置。
  - [SetAtomicType](../atomic_operations/set_atomic_type.md)
  - [DisableDmaAtomic](../atomic_operations/disable_dma_atomic.md)
  - [SetAtomicAdd](../atomic_operations/set_atomic_add.md)
  - [SetAtomicMax](../atomic_operations/set_atomic_max_isasi.md)
  - [SetAtomicMin](../atomic_operations/set_atomic_min_isasi.md)


## 调用示例

- 如下示例中开启非饱和模式，数据类型为half。

    ```cpp
    AscendC::SetCtrlSpr<48, 48>(1);
    ```

- <a name="example2"></a>原子操作中，half类型配置全局非饱和模式示例。

    ```cpp
    AscendC::SetCtrlSpr<6, 8>(2);
    AscendC::SetAtomicAdd<half>();
    AscendC::DataCacheCleanAndInvalid<half, AscendC::CacheLine::ENTIRE_DATA_CACHE, AscendC::DcciDst::CACHELINE_ATOMIC>(dstTensor);
    AscendC::SetCtrlSpr<48, 48>(1);
    ...
    ```

更多示例请参考[CtrlSpr样例](https://gitcode.com/cann/asc-devkit/tree/885973fe9fd42a600e3551af9bc11a279e6f183b/examples/01_simd_cpp_api/03_basic_api/09_utils/ctrl_spr)。


<!-- cannbot:related:start -->
## 相关

- [GetCtrlSpr](get_ctrl_spr_isasi.md)（`related`）：“读取CTRL寄存器（控制寄存器）特定比特位上的值。”；“对CTRL寄存器（控制寄存器）的特定比特位进行设置。通过模板参数startBit和endBit指定目标比特位范围，将运行参数value（超出比特位范围会出现编译报错）写入CTRL寄存器对应位置。”。两接口以相同 bit range 形成 CTRL 配置写入与回读核验链。
- [InplacePowTensorScalar 950 ACLNN 算子知识](../../../../operators/aclnn/math/math/inplace_pow_tensor_scalar_950.md)（`related`）：e==2/3 -> SAT bit60=0; masked multiply (u8/s8 widen to 16-bit); restore bit60=1；Ascend 950PR/Ascend 950DT仅支持CTRL［8:6］、CTRL［10:9］、CTRL［45］、CTRL［48］、CTRL［50］、CTRL［53］、CTRL［59］、CTRL［60］比特位。；候选为平方和立方专用 helper 的 CTRL［60］ 保存恢复提供接口边界。
- [Reset](../resource_management/t_pipe/reset.md)（`related`）：针对Ascend 950PR/Ascend 950DT，调用该接口后，CTRL［48］保持原值，CTRL［60］复位为1。CTRL寄存器比特位说明请见SetCtrlSpr。；对CTRL寄存器（控制寄存器）的特定比特位进行设置。通过模板参数startBit和endBit指定目标比特位范围，将运行参数value（超出比特位范围会出现编译报错）写入CTRL寄存器对应位置。；焦点给出 Reset 对 CTRL 位的副作用，目标提供这些位的显式读取边界与恢复设置入口。
- [ResetCtrlSpr](reset_ctrl_spr_isasi.md)（`same_topic`）：“对CTRL寄存器（控制寄存器）的特定比特位做重置。由模板参数［startBit, endBit］指定的比特位重置为默认值，默认值参考表 常用CTRL寄存器比特位说明。”与“对CTRL寄存器（控制寄存器）的特定比特位进行设置。通过模板参数startBit和endBit指定目标比特位范围，将运行参数value（超出比特位范围会出现编译报错）写入CTRL寄存器对应位置。”提供双方正文证据。SetCtrlSpr 写指定 CTRL 位段，ResetCtrlSpr 将同一位段恢复默认值，构成控制寄存器配置与清理的生命周期闭环。

<!-- cannbot:api-operator:start -->
### 源码中使用此 API 的算子（部分算子）

展示 10 / 44 个已匹配算子；每个 API 最多展示 10 个自动关联。
范围为算子卡声明的固定版本源码文件中的直接调用，不代表所有编译分支均执行，也不保证覆盖间接调用。

- [InplaceDivs 950 ACLNN 算子知识](../../../../operators/aclnn/math/math/inplace_divs_950.md)（`related`）：算子声明的固定版本源码包含对 `SetCtrlSpr(...)` 的直接调用（第 72 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/math/muls/op_kernel/arch35/muls_dag.h#L72)
- [GeluQuant 950 ACLNN 算子知识](../../../../operators/aclnn/nn/activation/gelu_quant_950.md)（`related`）：算子声明的固定版本源码包含对 `SetCtrlSpr(...)` 的直接调用（第 88 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/activation/gelu_quant/op_kernel/arch35/gelu_quant_base_regbase.h#L88)
- [MlaProlog A2/A3 ACLNN 算子知识](../../../../operators/aclnn/transformer/attention/mla_prolog.md)（`related`）：算子声明的固定版本源码包含对 `SetCtrlSpr(...)` 的直接调用（第 93 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/attention/mla_prolog_v3/op_kernel/mla_prolog_v3.cpp#L93)
- [PowTensorTensor 950 ACLNN 算子知识](../../../../operators/aclnn/math/math/pow_tensor_tensor_950.md)（`related`）：算子声明的固定版本源码包含对 `SetCtrlSpr(...)` 的直接调用（第 197 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/math/pow/op_kernel/arch35/pow_tensor_scalar_integer.h#L197)
- [SwigluGroupQuant 950 ACLNN 算子知识](../../../../operators/aclnn/nn/activation/swiglu_group_quant_950.md)（`related`）：算子声明的固定版本源码包含对 `SetCtrlSpr(...)` 的直接调用（第 68 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/activation/swiglu_group_quant/op_kernel/arch35/swiglu_group_quant_perf.h#L68)
- [MlaProlog 950 ACLNN 算子知识](../../../../operators/aclnn/transformer/attention/mla_prolog_950.md)（`related`）：算子声明的固定版本源码包含对 `SetCtrlSpr(...)` 的直接调用（第 93 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/attention/mla_prolog_v3/op_kernel/mla_prolog_v3.cpp#L93)
- [SimThreadExponential 950 ACLNN 算子知识](../../../../operators/aclnn/math/random/sim_thread_exponential_950.md)（`related`）：算子声明的固定版本源码包含对 `SetCtrlSpr(...)` 的直接调用（第 111 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/random/random_common/op_kernel/arch35/random_kernel_base.h#L111)
- [InplaceQuantScatter 950 ACLNN 算子知识](../../../../operators/aclnn/nn/index/inplace_quant_scatter_950.md)（`related`）：算子声明的固定版本源码包含对 `SetCtrlSpr(...)` 的直接调用（第 67 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/index/quant_update_scatter/op_kernel/arch35/quant_update_scatter_base.h#L67)
- [grouped_matmul_swiglu_quant 950 ACLNN 算子知识](../../../../operators/aclnn/transformer/gmm/grouped_matmul_swiglu_quant_950.md)（`related`）：算子声明的固定版本源码包含对 `SetCtrlSpr(...)` 的直接调用（第 74 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/gmm/grouped_matmul_swiglu_quant_v2/op_kernel/grouped_matmul_swiglu_quant_v2_apt.cpp#L74)
- [RotateQuant 950 ACLNN 算子知识](../../../../operators/aclnn/nn/matmul/rotate_quant_950.md)（`related`）：算子声明的固定版本源码包含对 `SetCtrlSpr(...)` 的直接调用（第 67 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/matmul/common/cmct/epilogue/block_epilogue_rotate_quant.h#L67)

<!-- cannbot:api-operator:end -->
<!-- cannbot:related:end -->
