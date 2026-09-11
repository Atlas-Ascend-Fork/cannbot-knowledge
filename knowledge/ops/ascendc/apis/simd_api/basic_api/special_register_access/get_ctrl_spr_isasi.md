---
type: API
title: GetCtrlSpr
description: 读取CTRL寄存器特定比特位上的值。
tags:
- task.lookup
- topic.implementation.api_layer.basic_api
- topic.programming_model.system_variable
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/special_register_access/GetCtrlSpr_ISASI.md
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

# GetCtrlSpr(ISASI)

## 功能说明

头文件路径为：`"basic_api/kernel_operator_common_intf.h"`。

读取CTRL寄存器（控制寄存器）特定比特位上的值。

## 函数原型

```cpp
template <int8_t startBit, int8_t endBit>
__aicore__ static inline int64_t GetCtrlSpr()
```

## 参数说明

**表1** 模板参数说明

| 参数名 | 描述 |
| --- | --- |
| startBit | 起始比特位索引。 |
| endBit | 终止比特位索引。 |

## 数据类型

本接口为寄存器访问接口，不涉及张量数据类型操作。返回值类型固定为int64_t。

## 返回值说明

CTRL寄存器对应比特位上的值。

## 约束说明

- startBit和endBit的取值范围为[0, 63]。
- startBit小于等于endBit。
- 各比特位的说明请参考[SetCtrlSpr(ISASI)参数说明](set_ctrl_spr_isasi.md#参数说明)。

## 调用示例

如下为读取CTRL[48]比特位数值的示例。

```cpp
int64_t valueCtrlAfterSet = AscendC::GetCtrlSpr<48, 48>();
```

更多示例请参考[CtrlSpr样例](https://gitcode.com/cann/asc-devkit/tree/885973fe9fd42a600e3551af9bc11a279e6f183b/examples/01_simd_cpp_api/03_basic_api/09_utils/ctrl_spr)。


<!-- cannbot:related:start -->
## 相关

- [ResetCtrlSpr](reset_ctrl_spr_isasi.md)（`related`）：“读取CTRL寄存器（控制寄存器）特定比特位上的值。”；“对CTRL寄存器（控制寄存器）的特定比特位做重置。由模板参数［startBit, endBit］指定的比特位重置为默认值，默认值参考表 常用CTRL寄存器比特位说明。”。Reset 后可用 GetCtrlSpr 对同一 bit range 回读默认值，闭合临时控制位的恢复验证。
- [SetCtrlSpr](set_ctrl_spr_isasi.md)（`related`）：“读取CTRL寄存器（控制寄存器）特定比特位上的值。”；“对CTRL寄存器（控制寄存器）的特定比特位进行设置。通过模板参数startBit和endBit指定目标比特位范围，将运行参数value（超出比特位范围会出现编译报错）写入CTRL寄存器对应位置。”。两接口以相同 bit range 形成 CTRL 配置写入与回读核验链。

<!-- cannbot:api-operator:start -->
### 源码中使用此 API 的算子（部分算子）

展示 10 / 35 个已匹配算子；每个 API 最多展示 10 个自动关联。
范围为算子卡声明的固定版本源码文件中的直接调用，不代表所有编译分支均执行，也不保证覆盖间接调用。

- [GeluQuant 950 ACLNN 算子知识](../../../../operators/aclnn/nn/activation/gelu_quant_950.md)（`related`）：算子声明的固定版本源码包含对 `GetCtrlSpr(...)` 的直接调用（第 111 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/activation/gelu_quant/op_kernel/gelu_quant_apt.cpp#L111)
- [MlaProlog A2/A3 ACLNN 算子知识](../../../../operators/aclnn/transformer/attention/mla_prolog.md)（`related`）：算子声明的固定版本源码包含对 `GetCtrlSpr(...)` 的直接调用（第 72 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/attention/mla_prolog_v3/op_kernel/mla_prolog_v3.cpp#L72)
- [SwigluGroupQuant 950 ACLNN 算子知识](../../../../operators/aclnn/nn/activation/swiglu_group_quant_950.md)（`related`）：算子声明的固定版本源码包含对 `GetCtrlSpr(...)` 的直接调用（第 42 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/activation/swiglu_group_quant/op_kernel/swiglu_group_quant.cpp#L42)
- [MlaProlog 950 ACLNN 算子知识](../../../../operators/aclnn/transformer/attention/mla_prolog_950.md)（`related`）：算子声明的固定版本源码包含对 `GetCtrlSpr(...)` 的直接调用（第 72 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/attention/mla_prolog_v3/op_kernel/mla_prolog_v3.cpp#L72)
- [InplaceQuantScatter 950 ACLNN 算子知识](../../../../operators/aclnn/nn/index/inplace_quant_scatter_950.md)（`related`）：算子声明的固定版本源码包含对 `GetCtrlSpr(...)` 的直接调用（第 38 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/index/quant_update_scatter/op_kernel/quant_update_scatter_apt.cpp#L38)
- [grouped_matmul_swiglu_quant 950 ACLNN 算子知识](../../../../operators/aclnn/transformer/gmm/grouped_matmul_swiglu_quant_950.md)（`related`）：算子声明的固定版本源码包含对 `GetCtrlSpr(...)` 的直接调用（第 72 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/gmm/grouped_matmul_swiglu_quant_v2/op_kernel/grouped_matmul_swiglu_quant_v2_apt.cpp#L72)
- [AddRmsNorm 950 ACLNN 算子知识](../../../../operators/aclnn/nn/norm/add_rms_norm_950.md)（`related`）：算子声明的固定版本源码包含对 `GetCtrlSpr(...)` 的直接调用（第 53 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/norm/rms_norm/op_kernel/arch35/rms_norm_regbase_common.h#L53)
- [MoeDistributeCombine A2/A3 ACLNN 算子知识](../../../../operators/aclnn/transformer/mc2/moe_distribute_combine.md)（`related`）：算子声明的固定版本源码包含对 `GetCtrlSpr(...)` 的直接调用（第 86 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/mc2/moe_distribute_combine_v2/op_kernel/moe_distribute_combine_v2.cpp#L86)
- [AddRmsNormDynamicMxQuant 950 ACLNN 算子知识](../../../../operators/aclnn/nn/norm/add_rms_norm_dynamic_mx_quant_950.md)（`related`）：算子声明的固定版本源码包含对 `GetCtrlSpr(...)` 的直接调用（第 44 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/norm/add_rms_norm_dynamic_mx_quant/op_kernel/add_rms_norm_dynamic_mx_quant_apt.cpp#L44)
- [MoeDistributeDispatch A2/A3 ACLNN 算子知识](../../../../operators/aclnn/transformer/mc2/moe_distribute_dispatch.md)（`related`）：算子声明的固定版本源码包含对 `GetCtrlSpr(...)` 的直接调用（第 62 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/mc2/moe_distribute_dispatch_v2/op_kernel/moe_distribute_dispatch_v2.cpp#L62)

<!-- cannbot:api-operator:end -->
<!-- cannbot:related:end -->
